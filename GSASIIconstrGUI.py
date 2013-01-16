# -*- coding: utf-8 -*-
#GSASIIconstrGUI - constraint GUI routines
########### SVN repository information ###################
# $Date: 2012-12-05 15:38:26 -0600 (Wed, 05 Dec 2012) $
# $Author: vondreele $
# $Revision: 810 $
# $URL: https://subversion.xor.aps.anl.gov/pyGSAS/trunk/GSASIIconstrGUI.py $
# $Id: GSASIIconstrGUI.py 810 2012-12-05 21:38:26Z vondreele $
########### SVN repository information ###################
import sys
import wx
import wx.grid as wg
import time
import random as ran
import numpy as np
import numpy.ma as ma
import os.path
import GSASIIpath
GSASIIpath.SetVersionNumber("$Revision: 810 $")
import GSASIIElem as G2elem
import GSASIIElemGUI as G2elemGUI
import GSASIIphsGUI as G2phG
import GSASIIstruct as G2str
import GSASIImapvars as G2mv
import GSASIIgrid as G2gd
import GSASIIplot as G2plt
VERY_LIGHT_GREY = wx.Colour(235,235,235)

class MultiIntegerDialog(wx.Dialog):
    
    def __init__(self,parent,title,prompts,values):
        wx.Dialog.__init__(self,parent,-1,title, 
            pos=wx.DefaultPosition,style=wx.DEFAULT_DIALOG_STYLE)
        self.panel = wx.Panel(self)         #just a dummy - gets destroyed in Draw!
        self.values = values
        self.prompts = prompts
        self.Draw()
        
    def Draw(self):
        
        def OnValItem(event):
            Obj = event.GetEventObject()
            ind = Indx[Obj.GetId()]
            try:
                val = int(Obj.GetValue())
                if val <= 0:
                    raise ValueError
            except ValueError:
                val = self.values[ind]
            self.values[ind] = val
            Obj.SetValue('%d'%(val))
            
        self.panel.Destroy()
        self.panel = wx.Panel(self)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        Indx = {}
        for ival,[prompt,value] in enumerate(zip(self.prompts,self.values)):
            mainSizer.Add(wx.StaticText(self.panel,-1,prompt),0,wx.ALIGN_CENTER)
            valItem = wx.TextCtrl(self.panel,-1,value='%d'%(value),style=wx.TE_PROCESS_ENTER)
            mainSizer.Add(valItem,0,wx.ALIGN_CENTER)
            Indx[valItem.GetId()] = ival
            valItem.Bind(wx.EVT_TEXT_ENTER,OnValItem)
            valItem.Bind(wx.EVT_KILL_FOCUS,OnValItem)
        OkBtn = wx.Button(self.panel,-1,"Ok")
        OkBtn.Bind(wx.EVT_BUTTON, self.OnOk)
        CancelBtn = wx.Button(self.panel,-1,'Cancel')
        CancelBtn.Bind(wx.EVT_BUTTON, self.OnCancel)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((20,20),1)
        btnSizer.Add(OkBtn)
        btnSizer.Add(CancelBtn)
        btnSizer.Add((20,20),1)
        mainSizer.Add(btnSizer,0,wx.EXPAND|wx.BOTTOM|wx.TOP, 10)
        self.panel.SetSizer(mainSizer)
        self.panel.Fit()
        self.Fit()

    def GetValues(self):
        return self.values
        
    def OnOk(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_OK)              
        
    def OnCancel(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_CANCEL)
        
################################################################################
#####  Constraints
################################################################################           
       
def UpdateConstraints(G2frame,data):
    '''Called when Constraints tree item is selected.
    Displays the constraints in the data window
    '''
    if not data:
        data.update({'Hist':[],'HAP':[],'Phase':[]})       #empty dict - fill it
    Histograms,Phases = G2frame.GetUsedHistogramsAndPhasesfromTree()
    AtomDict = dict([Phases[phase]['pId'],Phases[phase]['Atoms']] for phase in Phases)
    Natoms,atomIndx,phaseVary,phaseDict,pawleyLookup,FFtable,BLtable = G2str.GetPhaseData(Phases,Print=False)
    phaseList = []
    for item in phaseDict:
        if item.split(':')[2] not in ['Ax','Ay','Az','Amul','AI/A','Atype','SHorder']:
            phaseList.append(item)
    phaseList.sort()
    phaseAtNames = {}
    phaseAtTypes = {}
    TypeList = []
    for item in phaseList:
        Split = item.split(':')
        if Split[2][:2] in ['AU','Af','dA']:
            Id = int(Split[0])
            phaseAtNames[item] = AtomDict[Id][int(Split[3])][0]
            phaseAtTypes[item] = AtomDict[Id][int(Split[3])][1]
            if phaseAtTypes[item] not in TypeList:
                TypeList.append(phaseAtTypes[item])
        else:
            phaseAtNames[item] = ''
            phaseAtTypes[item] = ''
            
    hapVary,hapDict,controlDict = G2str.GetHistogramPhaseData(Phases,Histograms,Print=False)
    hapList = hapDict.keys()
    hapList.sort()
    histVary,histDict,controlDict = G2str.GetHistogramData(Histograms,Print=False)
    histList = []
    for item in histDict:
        if item.split(':')[2] not in ['Omega','Type','Chi','Phi','Azimuth','Gonio. radius','Lam1','Lam2','Back']:
            histList.append(item)
    histList.sort()
    Indx = {}
    scope = {}                          #filled out later
    G2frame.Page = [0,'phs']
    
    def GetPHlegends(Phases,Histograms):
        plegend = '\n In p::name'
        hlegend = '\n In :h:name'
        phlegend = '\n In p:h:name'
        for phase in Phases:
            plegend += '\n p:: = '+str(Phases[phase]['pId'])+':: for '+phase
            count = 0
            for histogram in Phases[phase]['Histograms']:
                if count < 3:
                    phlegend += '\n p:h: = '+str(Phases[phase]['pId'])+':'+str(Histograms[histogram]['hId'])+': for '+phase+' in '+histogram
                else:
                    phlegend += '\n ... etc.'
                    break
                count += 1
        count = 0
        for histogram in Histograms:
            if count < 3:
                hlegend += '\n :h: = :'+str(Histograms[histogram]['hId'])+': for '+histogram
            else:
                hlegend += '\n ... etc.'
                break
            count += 1
        return plegend,hlegend,phlegend
        
    def FindEquivVarb(name,nameList):
        outList = []
        phlist = []
        items = name.split(':')
        namelist = [items[2],]
        if 'dA' in name:
            namelist = ['dAx','dAy','dAz']
        elif 'AU' in name:
            namelist = ['AUiso','AU11','AU22','AU33','AU12','AU13','AU23']
        for item in nameList:
            keys = item.split(':')
            if keys[0] not in phlist:
                phlist.append(keys[0])
            if keys[2] in namelist and item != name:
                outList.append(item)
        if items[1]:
            for key in phlist:
                outList.append(key+':all:'+items[2])
        return outList
        
    def SelectVarbs(page,FrstVarb,varList,legend,constType):
        '''Select variables used in Constraints after one variable has
        been selected which determines the appropriate variables to be
        used here. Then creates the constraint and adds it to the
        constraints list.
        Called from OnAddEquivalence, OnAddFunction & OnAddConstraint
        '''
        #future -  add 'all:all:name', '0:all:name', etc. to the varList
        if page[1] == 'phs':
            atchoice = [item+' for '+phaseAtNames[item] for item in varList]
            atchoice += [FrstVarb+' for all']
            atchoice += [FrstVarb+' for all '+atype for atype in TypeList]
            dlg = wx.MultiChoiceDialog(G2frame,'Select more variables:'+legend,
                'Constrain '+FrstVarb+' and...',atchoice)
        else:
            dlg = wx.MultiChoiceDialog(G2frame,'Select more variables:'+legend,
                'Constrain '+FrstVarb+' and...',varList)
        varbs = [FrstVarb,]
        if dlg.ShowModal() == wx.ID_OK:
            sel = dlg.GetSelections()
            try:
                for x in sel:
                    if ':all:' in varList[x]:       #a histogram 'all' - supercedes any individual selection
                        varbs = [FrstVarb,]
                        items = varList[x].split(':')
                        for item in varList:
                            if items[0] == item.split(':')[0] and ':all:' not in item:
                                varbs.append(item)
                        break
                    else:
                        varbs.append(varList[x])
            except IndexError:      # one of the 'all' chosen - supercedes any individual selection
                varbs = [FrstVarb,]
                Atypes = []
                for x in sel:
                    item = atchoice[x]
                    if 'all' in item:
                        Atypes.append(item.split('all')[1].strip())
                if '' in Atypes:
                    varbs += varList
                else:
                    for item in varList:
                        if phaseAtTypes[item] in Atypes:
                            varbs.append(item)  
        dlg.Destroy()
        if len(varbs) > 1:
            if 'equivalence' in constType:
                constr = [[1.0,FrstVarb]]
                for item in varbs[1:]:
                    constr += [[1.0,item]]
                return [constr+[None,None,'e']]      # list of equivalent variables & mults
            elif 'function' in constType:
                constr = map(list,zip([1.0 for i in range(len(varbs))],varbs))
                return [constr+[None,False,'f']]         #just one constraint
            else:       #'constraint'
                constr = map(list,zip([1.0 for i in range(len(varbs))],varbs))
                return [constr+[1.0,None,'c']]          #just one constraint - default sum to one
        return []

    def CheckAddedConstraint(newcons):
        '''Check a new constraint that has just been input.
        If there is an error display a message and give the user a
        choice to keep or discard the last entry (why keep? -- they
        may want to delete something else or edit multipliers).
        Since the varylist is not available, no warning messages
        should be generated.
        Returns True if constraint should be added
        '''
        allcons = []
        for key in 'Hist','HAP','Phase':
            allcons += data[key]
        allcons += newcons
        if not len(allcons): return True
        G2mv.InitVars()    
        constDictList,fixedList,ignored = G2str.ProcessConstraints(allcons)
        errmsg, warnmsg = G2mv.CheckConstraints('',constDictList,fixedList)
        if errmsg:
            res = G2frame.ErrorDialog('Constraint Error',
                'Error with newly added constraint:\n'+errmsg+
                '\n\nDiscard newly added constraint?',parent=G2frame.dataFrame,
                wtype=wx.YES_NO)
            return res != wx.ID_YES
        elif warnmsg:
            print 'Unexpected contraint warning:\n',warnmsg
        return True

    def CheckChangedConstraint():
        '''Check all constraints after an edit has been made.
        If there is an error display a message and give the user a
        choice to keep or discard the last edit.
        Since the varylist is not available, no warning messages
        should be generated.
        Returns True if the edit should be retained
        '''
        allcons = []
        for key in 'Hist','HAP','Phase':
            allcons += data[key]
        if not len(allcons): return True
        G2mv.InitVars()    
        constDictList,fixedList,ignored = G2str.ProcessConstraints(allcons)
        errmsg, warnmsg = G2mv.CheckConstraints('',constDictList,fixedList)
        if errmsg:
            res = G2frame.ErrorDialog('Constraint Error',
                'Error after editing constraint:\n'+errmsg+
                '\n\nDiscard last constraint edit?',parent=G2frame.dataFrame,
                wtype=wx.YES_NO)
            return res != wx.ID_YES
        elif warnmsg:
            print 'Unexpected contraint warning:\n',warnmsg
        return True
             
    def OnAddHold(event):
        '''add a Hold constraint'''
        for phase in Phases:
            Phase = Phases[phase]
            Atoms = Phase['Atoms']
        constr = []
        page = G2frame.Page
        choice = scope[page[1]]
        if page[1] == 'phs':
            atchoice = [item+' for '+phaseAtNames[item] for item in choice[2]]
            dlg = wx.SingleChoiceDialog(G2frame,'Select 1st variable:'+choice[1],choice[0],atchoice)
        else:    
            dlg = wx.SingleChoiceDialog(G2frame,'Select 1st variable:'+choice[1],choice[0],choice[2])
        if dlg.ShowModal() == wx.ID_OK:
            sel = dlg.GetSelection()
            FrstVarb = choice[2][sel]
            newcons = [[[0.0,FrstVarb],None,None,'h']]
            if CheckAddedConstraint(newcons):
                data[choice[3]] += newcons
        dlg.Destroy()
        choice[4]()
        
    def OnAddEquivalence(event):
        '''add an Equivalence constraint'''
        constr = []
        page = G2frame.Page
        choice = scope[page[1]]
        if page[1] == 'phs':
            atchoice = [item+' for '+phaseAtNames[item] for item in choice[2]]
            dlg = wx.SingleChoiceDialog(G2frame,'Select 1st variable:'+choice[1],choice[0],atchoice)
        else:    
            dlg = wx.SingleChoiceDialog(G2frame,'Select 1st variable:'+choice[1],choice[0],choice[2])
        if dlg.ShowModal() == wx.ID_OK:
            sel = dlg.GetSelection()
            FrstVarb = choice[2][sel]
            moreVarb = FindEquivVarb(FrstVarb,choice[2])
            newcons = SelectVarbs(page,FrstVarb,moreVarb,choice[1],'equivalence')
            if len(newcons) > 0:
                if CheckAddedConstraint(newcons):
                    data[choice[3]] += newcons
        dlg.Destroy()
        choice[4]()
   
    def OnAddFunction(event):
        '''add a Function (new variable) constraint'''
        constr = []
        page = G2frame.Page
        choice = scope[page[1]]
        if page[1] == 'phs':
            atchoice = [item+' for '+phaseAtNames[item] for item in choice[2]]
            dlg = wx.SingleChoiceDialog(G2frame,'Select 1st variable:'+choice[1],choice[0],atchoice)
        else:    
            dlg = wx.SingleChoiceDialog(G2frame,'Select 1st variable:'+choice[1],choice[0],choice[2])
        if dlg.ShowModal() == wx.ID_OK:
            sel = dlg.GetSelection()
            FrstVarb = choice[2][sel]
            moreVarb = FindEquivVarb(FrstVarb,choice[2])
            newcons = SelectVarbs(page,FrstVarb,moreVarb,choice[1],'function')
            if len(newcons) > 0:
                if CheckAddedConstraint(newcons):
                    data[choice[3]] += newcons
        dlg.Destroy()
        choice[4]()
                        
    def OnAddConstraint(event):
        '''add a constraint equation to the constraints list'''
        constr = []
        page = G2frame.Page
        choice = scope[page[1]]
        if page[1] == 'phs':
            atchoice = [item+' for '+phaseAtNames[item] for item in choice[2]]
            dlg = wx.SingleChoiceDialog(G2frame,'Select 1st variable:'+choice[1],choice[0],atchoice)
        else:    
            dlg = wx.SingleChoiceDialog(G2frame,'Select 1st variable:'+choice[1],choice[0],choice[2])
        if dlg.ShowModal() == wx.ID_OK:
            sel = dlg.GetSelection()
            FrstVarb = choice[2][sel]
            moreVarb = FindEquivVarb(FrstVarb,choice[2])
            newcons = SelectVarbs(page,FrstVarb,moreVarb,choice[1],'constraint')
            if len(newcons) > 0:
                if CheckAddedConstraint(newcons):
                    data[choice[3]] += newcons
        dlg.Destroy()
        choice[4]()
                        
    def ConstSizer(name,pageDisplay):
        '''This creates a sizer displaying all of the constraints entered
        '''
        constSizer = wx.FlexGridSizer(1,4,0,0)
        maxlen = 70 # characters before wrapping a constraint
        for Id,item in enumerate(data[name]):
            eqString = ['',]
            if item[-1] == 'h':
                constSizer.Add((5,5),0)              # blank space for edit button
                typeString = ' FIXED   '
                eqString[-1] = item[0][1]+'   '
            elif isinstance(item[-1],str):
                constEdit = wx.Button(pageDisplay,-1,'Edit',style=wx.BU_EXACTFIT)
                constEdit.Bind(wx.EVT_BUTTON,OnConstEdit)
                constSizer.Add(constEdit)            # edit button
                Indx[constEdit.GetId()] = [Id,name]
                if item[-1] == 'f':
                    for term in item[:-3]:
                        if len(eqString[-1]) > maxlen:
                            eqString.append(' ')
                        m = term[0]
                        if eqString[-1] != '':
                            if m >= 0:
                                eqString[-1] += ' + '
                            else:
                                eqString[-1] += ' - '
                                m = abs(m)
                        eqString[-1] += '%.3f*%s '%(m,term[1])
                    typeString = ' NEWVAR  '
                    eqString[-1] += ' = New Variable   '
                elif item[-1] == 'c':
                    for term in item[:-3]:
                        if len(eqString[-1]) > maxlen:
                            eqString.append(' ')
                        if eqString[-1] != '':
                            if term[0] > 0:
                                eqString[-1] += ' + '
                            else:
                                eqString[-1] += ' - '
                        eqString[-1] += '%.3f*%s '%(abs(term[0]),term[1])
                    typeString = ' CONSTR  '
                    eqString[-1] += ' = %.3f'%(item[-3])+'  '
                elif item[-1] == 'e':
                    for term in item[:-3]:
                        if term[0] == 0: term[0] = 1.0
                        if len(eqString[-1]) > maxlen:
                            eqString.append(' ')
                        if eqString[-1] == '':
                            eqString[-1] += '%s '%(term[1])
                            first = term[0]
                        else:
                            eqString[-1] += ' = %.3f*%s '%(first/term[0],term[1])
                    typeString = ' EQUIV   '
                else:
                    print 'Unexpected constraint',item
            else:
                print 'Removing old-style constraints'
                data[name] = []
                return constSizer
            constDel = wx.Button(pageDisplay,-1,'Delete',style=wx.BU_EXACTFIT)
            constDel.Bind(wx.EVT_BUTTON,OnConstDel)
            Indx[constDel.GetId()] = [Id,name]
            constSizer.Add(constDel)             # delete button
            constSizer.Add(wx.StaticText(pageDisplay,-1,typeString),0,wx.ALIGN_CENTER_VERTICAL)
            EqSizer = wx.BoxSizer(wx.VERTICAL)
            for s in eqString:
                EqSizer.Add(wx.StaticText(pageDisplay,-1,s),0,wx.ALIGN_CENTER_VERTICAL)
            constSizer.Add(EqSizer,0,wx.ALIGN_CENTER_VERTICAL)
            # if item[-1] == 'f':
            #     constRef = wx.CheckBox(pageDisplay,-1,label=' Refine?') 
            #     constRef.SetValue(item[-2])
            #     constRef.Bind(wx.EVT_CHECKBOX,OnConstRef)
            #     Indx[constRef.GetId()] = item
            #     constSizer.Add(constRef)
            # else:
            #     constSizer.Add((5,5),0)
        return constSizer
                
    # def OnConstRef(event):
    #     Obj = event.GetEventObject()
    #     Indx[Obj.GetId()][-2] = Obj.GetValue()
        
    def OnConstDel(event):
        Obj = event.GetEventObject()
        Id,name = Indx[Obj.GetId()]
        del(data[name][Id])
        OnPageChanged(None)        
        
    def OnConstEdit(event):
        '''Called to edit an individual contraint by the Edit button'''
        Obj = event.GetEventObject()
        Id,name = Indx[Obj.GetId()]
        sep = '*'
        if data[name][Id][-1] == 'f':
            items = data[name][Id][:-3]+[[],]
            constType = 'New Variable'
            lbl = 'Enter value for each term in constraint; sum = new variable'
        elif data[name][Id][-1] == 'c':
            items = data[name][Id][:-3]+[
                [data[name][Id][-3],'fixed value ='],[]]
            constType = 'Constraint'
            lbl = 'Edit value for each term in constant constraint sum'
        elif data[name][Id][-1] == 'e':
            items = data[name][Id][:-3]+[[],]
            constType = 'Equivalence'
            lbl = 'The following terms are set to be equal:'
            sep = '/'
        else:
            return
        dlg = G2frame.ConstraintDialog(G2frame.dataFrame,constType,lbl,items,sep)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                prev = data[name][Id]
                result = dlg.GetData()
                if data[name][Id][-1] == 'c':
                    data[name][Id][:-3] = result[:-2]
                    data[name][Id][-3] = result[-2][0]
                else:
                    data[name][Id][:-3] = result[:-1]
                if not CheckChangedConstraint():
                    data[name][Id] = prev
        except:
            import traceback
            print traceback.format_exc()
        finally:
            dlg.Destroy()            
        OnPageChanged(None)                     
    
    def UpdateHAPConstr():
        '''Responds to press on Histogram/Phase Constraints tab,
        shows constraints in data window'''
        HAPConstr.DestroyChildren()
        HAPDisplay = wx.Panel(HAPConstr)
        HAPSizer = wx.BoxSizer(wx.VERTICAL)
        HAPSizer.Add((5,5),0)
        HAPSizer.Add(ConstSizer('HAP',HAPDisplay))
        HAPDisplay.SetSizer(HAPSizer,True)
        Size = HAPSizer.GetMinSize()
        Size[0] += 40
        Size[1] = max(Size[1],250) + 20
        HAPDisplay.SetSize(Size)
        # scroll bar not working, at least not on Mac
        HAPConstr.SetScrollbars(10,10,Size[0]/10-4,Size[1]/10-1)
        Size[1] = min(Size[1],250)
        G2frame.dataFrame.setSizePosLeft(Size)
        
    def UpdateHistConstr():
        '''Responds to press on Histogram Constraints tab,
        shows constraints in data window'''
        HistConstr.DestroyChildren()
        HistDisplay = wx.Panel(HistConstr)
        HistSizer = wx.BoxSizer(wx.VERTICAL)
        HistSizer.Add((5,5),0)        
        HistSizer.Add(ConstSizer('Hist',HistDisplay))
        HistDisplay.SetSizer(HistSizer,True)
        Size = HistSizer.GetMinSize()
        Size[0] += 40
        Size[1] = max(Size[1],250) + 20
        HistDisplay.SetSize(Size)
        HistConstr.SetScrollbars(10,10,Size[0]/10-4,Size[1]/10-1)
        Size[1] = min(Size[1],250)
        G2frame.dataFrame.setSizePosLeft(Size)
        
    def UpdatePhaseConstr():
        '''Responds to press on Phase Constraint tab,
        shows constraints in data window'''
        PhaseConstr.DestroyChildren()
        PhaseDisplay = wx.Panel(PhaseConstr)
        PhaseSizer = wx.BoxSizer(wx.VERTICAL)
        PhaseSizer.Add((5,5),0)        
        PhaseSizer.Add(ConstSizer('Phase',PhaseDisplay))
        PhaseDisplay.SetSizer(PhaseSizer,True)
        Size = PhaseSizer.GetMinSize()
        Size[0] += 40
        Size[1] = max(Size[1],250) + 20
        PhaseDisplay.SetSize(Size)
        PhaseConstr.SetScrollbars(10,10,Size[0]/10-4,Size[1]/10-1)
        Size[1] = min(Size[1],250)
        G2frame.dataFrame.setSizePosLeft(Size)
    
    def OnPageChanged(event):
        if event:       #page change event!
            page = event.GetSelection()
        else:
            page = G2frame.dataDisplay.GetSelection()
        oldPage = G2frame.dataDisplay.ChangeSelection(page)
        text = G2frame.dataDisplay.GetPageText(page)
        if text == 'Histogram/Phase constraints':
            G2frame.Page = [page,'hap']
            UpdateHAPConstr()
        elif text == 'Histogram constraints':
            G2frame.Page = [page,'hst']
            UpdateHistConstr()
        elif text == 'Phase constraints':
            G2frame.Page = [page,'phs']
            UpdatePhaseConstr()

    def SetStatusLine(text):
        Status.SetStatusText(text)                                      
        
    plegend,hlegend,phlegend = GetPHlegends(Phases,Histograms)
    scope = {'hst':['Histogram contraints:',hlegend,histList,'Hist',UpdateHistConstr],
        'hap':['Histogram * Phase contraints:',phlegend,hapList,'HAP',UpdateHAPConstr],
        'phs':['Phase contraints:',plegend,phaseList,'Phase',UpdatePhaseConstr]}
    if G2frame.dataDisplay:
        G2frame.dataDisplay.Destroy()
    G2gd.SetDataMenuBar(G2frame,G2frame.dataFrame.ConstraintMenu)
    G2frame.dataFrame.SetLabel('Constraints')
    if not G2frame.dataFrame.GetStatusBar():
        Status = G2frame.dataFrame.CreateStatusBar()
    SetStatusLine('')
    
    G2gd.SetDataMenuBar(G2frame,G2frame.dataFrame.ConstraintMenu)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnAddConstraint, id=G2gd.wxID_CONSTRAINTADD)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnAddFunction, id=G2gd.wxID_FUNCTADD)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnAddEquivalence, id=G2gd.wxID_EQUIVADD)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnAddHold, id=G2gd.wxID_HOLDADD)
    G2frame.dataDisplay = G2gd.GSNoteBook(parent=G2frame.dataFrame,size=G2frame.dataFrame.GetClientSize())
    
    PhaseConstr = wx.ScrolledWindow(G2frame.dataDisplay)
    G2frame.dataDisplay.AddPage(PhaseConstr,'Phase constraints')
    HAPConstr = wx.ScrolledWindow(G2frame.dataDisplay)
    G2frame.dataDisplay.AddPage(HAPConstr,'Histogram/Phase constraints')
    HistConstr = wx.ScrolledWindow(G2frame.dataDisplay)
    G2frame.dataDisplay.AddPage(HistConstr,'Histogram constraints')
    UpdatePhaseConstr()

    G2frame.dataDisplay.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, OnPageChanged)
    # validate all the constrants -- should not see any errors here normally
    allcons = []
    for key in 'Hist','HAP','Phase':
        allcons += data[key]
    if not len(allcons): return
    G2mv.InitVars()    
    constDictList,fixedList,ignored = G2str.ProcessConstraints(allcons)
    errmsg, warnmsg = G2mv.CheckConstraints('',constDictList,fixedList)
    if errmsg:
        G2frame.ErrorDialog('Constraint Error','Error in constraints:\n'+errmsg,
            parent=G2frame.dataFrame)
    elif warnmsg:
        print 'Unexpected contraint warning:\n',warnmsg
        
################################################################################
#### Rigid bodies
################################################################################

def UpdateRigidBodies(G2frame,data):
    '''Called when Rigid bodies tree item is selected.
    Displays the rigid bodies in the data window
    '''
    if not data:
        data.update({'Vector':{},'Residue':{},'Z-matrix':{}})       #empty dict - fill it
            
    Indx = {}
    plotDefaults = {'oldxy':[0.,0.],'Quaternion':[1.,0.,0.,0.],'cameraPos':20.,'viewDir':[0,0,1],}

    def OnPageChanged(event):
        if event:       #page change event!
            page = event.GetSelection()
        else:
            page = G2frame.dataDisplay.GetSelection()
        oldPage = G2frame.dataDisplay.ChangeSelection(page)
        text = G2frame.dataDisplay.GetPageText(page)
        if text == 'Vector rigid bodies':
            G2frame.Page = [page,'vrb']
            UpdateVectorRB()
        elif text == 'Residue rigid bodies':
            G2frame.Page = [page,'rrb']
            UpdateResidueRB()
        elif text == 'Z-matrix rigid bodies':
            G2frame.Page = [page,'zrb']
            UpdateZMatrixRB()
            
    def OnAddRigidBody(event):
        page = G2frame.dataDisplay.GetSelection()
        if 'Vector' in G2frame.dataDisplay.GetPageText(page):
            AddVectorRB()
        elif 'Residue' in G2frame.dataDisplay.GetPageText(page):
            AddResidueRB()
        elif 'Z-matrix' in G2frame.dataDisplay.GetPageText(page):
            AddZMatrixRB()
            
    def AddVectorRB():
        dlg = MultiIntegerDialog(G2frame.dataDisplay,'New Rigid Body',['No. atoms','No. translations'],[1,1])
        if dlg.ShowModal() == wx.ID_OK:
            nAtoms,nTrans = dlg.GetValues()
            vectorRB = data['Vector']
            rbId = ran.randint(0,sys.maxint)
            vecMag = [1.0 for i in range(nTrans)]
            vecRef = [False for i in range(nTrans)]
            vecVal = [np.zeros((nAtoms,3)) for j in range(nTrans)]
            rbTypes = ['C' for i in range(nAtoms)]
            Info = G2elem.GetAtomInfo('C')
            AtInfo= {'C':[Info['Drad'],Info['Color']]}
            data['Vector'][rbId] = {'RBname':'UNKRB','VectMag':vecMag,
                'VectRef':vecRef,'rbTypes':rbTypes,'rbVect':vecVal,'AtInfo':AtInfo}
        dlg.Destroy()
        UpdateVectorRB()
        
    def AddResidueRB():
        pass
        
    def AddZMatrixRB():
        pass

    def UpdateVectorRB():
        SetStatusLine(' You may use e.g. "sind(60)", "cos(60)", "c60" or "s60" for a vector entry')
        def rbNameSizer(rbId,rbData):

            def OnRBName(event):
                Obj = event.GetEventObject()
                rbId = Indx[Obj.GetId()]
                rbData['RBname'] = Obj.GetValue()
                
            def OnDelRB(event):
                Obj = event.GetEventObject()
                rbId = Indx[Obj.GetId()]
                del data['Vector'][rbId]
                wx.CallAfter(UpdateVectorRB)
                
            def OnPlotRB(event):
                Obj = event.GetEventObject()
                rbId = Indx[Obj.GetId()]
                Obj.SetValue(False)
                G2plt.PlotRigidBody(G2frame,'Vector',data['Vector'][rbId],plotDefaults)
            
            nameSizer = wx.BoxSizer(wx.HORIZONTAL)
            nameSizer.Add(wx.StaticText(VectorRBDisplay,-1,'Rigid body name: '),
                0,wx.ALIGN_CENTER_VERTICAL)
            RBname = wx.TextCtrl(VectorRBDisplay,-1,rbData['RBname'])
            Indx[RBname.GetId()] = rbId
            RBname.Bind(wx.EVT_TEXT_ENTER,OnRBName)
            RBname.Bind(wx.EVT_KILL_FOCUS,OnRBName)
            nameSizer.Add(RBname,0,wx.ALIGN_CENTER_VERTICAL)
            nameSizer.Add((5,0),)
            plotRB = wx.CheckBox(VectorRBDisplay,-1,'Plot?')
            Indx[plotRB.GetId()] = rbId
            plotRB.Bind(wx.EVT_CHECKBOX,OnPlotRB)
            nameSizer.Add(plotRB,0,wx.ALIGN_CENTER_VERTICAL)
            nameSizer.Add((5,0),)
            delRB = wx.CheckBox(VectorRBDisplay,-1,'Delete?')
            Indx[delRB.GetId()] = rbId
            delRB.Bind(wx.EVT_CHECKBOX,OnDelRB)
            nameSizer.Add(delRB,0,wx.ALIGN_CENTER_VERTICAL)
            return nameSizer
            
        def rbVectMag(rbId,imag,rbData):
            
            def OnRBVectorMag(event):
                Obj = event.GetEventObject()
                rbId,imag = Indx[Obj.GetId()]
                try:
                    val = float(Obj.GetValue())
                    if val <= 0.:
                        raise ValueError
                    rbData['VectMag'][imag] = val
                except ValueError:
                    pass
                Obj.SetValue('%8.3f'%(val))
                UpdateVectorRB()
                G2plt.PlotRigidBody(G2frame,'Vector',data['Vector'][rbId],plotDefaults)
                
            def OnRBVectorRef(event):
                Obj = event.GetEventObject()
                rbId,imag = Indx[Obj.GetId()]
                rbData['VectRef'][imag] = Obj.GetValue()
                        
            magSizer = wx.wx.BoxSizer(wx.HORIZONTAL)
            magSizer.Add(wx.StaticText(VectorRBDisplay,-1,'Translation magnitude: '),
                0,wx.ALIGN_CENTER_VERTICAL)
            magValue = wx.TextCtrl(VectorRBDisplay,-1,'%8.3f'%(rbData['VectMag'][imag]))
            Indx[magValue.GetId()] = [rbId,imag]
            magValue.Bind(wx.EVT_TEXT_ENTER,OnRBVectorMag)
            magValue.Bind(wx.EVT_KILL_FOCUS,OnRBVectorMag)
            magSizer.Add(magValue,0,wx.ALIGN_CENTER_VERTICAL)
            magSizer.Add((5,0),)
            magref = wx.CheckBox(VectorRBDisplay,-1,label=' Refine?') 
            magref.SetValue(rbData['VectRef'][imag])
            magref.Bind(wx.EVT_CHECKBOX,OnRBVectorRef)
            Indx[magref.GetId()] = [rbId,imag]
            magSizer.Add(magref,0,wx.ALIGN_CENTER_VERTICAL)
            return magSizer
            
        def OnRBVectorVal(event):
            Obj = event.GetEventObject()
            rbId,imag,i = Indx[Obj.GetId()]
            try:
                val = float(Obj.GetValue())
                data['Vector'][rbId]['rbVect'][imag][i] = val
            except ValueError:
                pass
            UpdateVectorRB()
            G2plt.PlotRigidBody(G2frame,'Vector',data['Vector'][rbId],plotDefaults)
            
        def rbVectors(rbId,imag,mag,XYZ,rbData):

            def TypeSelect(event):
                r,c = event.GetRow(),event.GetCol()
                if vecGrid.GetColLabelValue(c) == 'Type':
                    PE = G2elemGUI.PickElement(G2frame,oneOnly=True)
                    if PE.ShowModal() == wx.ID_OK:
                        if PE.Elem != 'None':
                            El = PE.Elem.strip().lower().capitalize()
                            if El not in rbData['rbRadii']:
                                rbData['rbRadii'][El] = G2elem.GetAtomInfo(El)['Drad']                            
                            rbData['rbTypes'][r] = El
                            vecGrid.SetCellValue(r,c,El)
                    PE.Destroy()

            def ChangeCell(event):
                r,c =  event.GetRow(),event.GetCol()
                if r >= 0 and (0 <= c < 3):
                    try:
                        val = float(vecGrid.GetCellValue(r,c))
                        rbData['rbVect'][imag][r][c] = val
                    except ValueError:
                        pass
                wx.CallAfter(UpdateVectorRB)

            vecSizer = wx.BoxSizer()
            Types = 3*[wg.GRID_VALUE_FLOAT+':10,5',]+[wg.GRID_VALUE_STRING,]+3*[wg.GRID_VALUE_FLOAT+':10,5',]
            colLabels = ['Vector x','Vector y','Vector z','Type','Cart x','Cart y','Cart z']
            table = []
            rowLabels = []
            for ivec,xyz in enumerate(rbData['rbVect'][imag]):
                table.append(list(xyz)+[rbData['rbTypes'][ivec],]+list(XYZ[ivec]))
                rowLabels.append(str(ivec))
            vecTable = G2gd.Table(table,rowLabels=rowLabels,colLabels=colLabels,types=Types)
            vecGrid = G2gd.GSGrid(VectorRBDisplay)
            vecGrid.SetTable(vecTable, True)
            vecGrid.Bind(wg.EVT_GRID_CELL_CHANGE, ChangeCell)
            vecGrid.Bind(wg.EVT_GRID_CELL_LEFT_DCLICK, TypeSelect)
            attr = wx.grid.GridCellAttr()
            attr.SetEditor(G2phG.GridFractionEditor(vecGrid))
            for c in range(3):
                vecGrid.SetColAttr(c, attr)
            for row in range(vecTable.GetNumberRows()):
                for col in [4,5,6]:
                    vecGrid.SetCellStyle(row,col,VERY_LIGHT_GREY,True)
            vecSizer.Add(vecGrid)
            return vecSizer
        
        VectorRB.DestroyChildren()
        VectorRBDisplay = wx.Panel(VectorRB)
        VectorRBSizer = wx.BoxSizer(wx.VERTICAL)
        for rbId in data['Vector']:
            rbData = data['Vector'][rbId]
            VectorRBSizer.Add(rbNameSizer(rbId,rbData),0)
            XYZ = np.array([[0.,0.,0.] for Ty in rbData['rbTypes']])
            for imag,mag in enumerate(rbData['VectMag']):
                XYZ += mag*rbData['rbVect'][imag]
                VectorRBSizer.Add(rbVectMag(rbId,imag,rbData),0)
                VectorRBSizer.Add(rbVectors(rbId,imag,mag,XYZ,rbData),0)
            VectorRBSizer.Add((5,5),0)        
        VectorRBSizer.Layout()    
        VectorRBDisplay.SetSizer(VectorRBSizer,True)
        Size = VectorRBSizer.GetMinSize()
        Size[0] += 40
        Size[1] = max(Size[1],250) + 20
        VectorRBDisplay.SetSize(Size)
        VectorRB.SetScrollbars(10,10,Size[0]/10-4,Size[1]/10-1)
#        Size[1] = min(Size[1],450)
        G2frame.dataFrame.setSizePosLeft(Size)
        
    def UpdateResidueRB():
        ResidueRB.DestroyChildren()
        ResidueRBDisplay = wx.Panel(ResidueRB)
        ResidueRBSizer = wx.BoxSizer(wx.VERTICAL)
        ResidueRBSizer.Add((5,5),0)        
#        VectorRBSizer.Add(ConstSizer('Phase',PhaseDisplay))
        ResidueRBSizer.Layout()    
        ResidueRBDisplay.SetSizer(ResidueRBSizer,True)
        Size = ResidueRBSizer.GetMinSize()
        Size[0] += 40
        Size[1] = max(Size[1],250) + 20
        ResidueRBDisplay.SetSize(Size)
        ResidueRB.SetScrollbars(10,10,Size[0]/10-4,Size[1]/10-1)
#        Size[1] = min(Size[1],250)
        G2frame.dataFrame.setSizePosLeft(Size)
        
    def UpdateZMatrixRB():
        ZMatrixRB.DestroyChildren()
        ZMatrixRBDisplay = wx.Panel(ZMatrixRB)
        ZMatrixRBSizer = wx.BoxSizer(wx.VERTICAL)
        ZMatrixRBSizer.Add((5,5),0)        
#        ZMatrixRBSizer.Add(ConstSizer('Phase',PhaseDisplay))
        ZMatrixRBSizer.Layout()    
        ZMatrixRBDisplay.SetSizer(ZMatrixRBSizer,True)
        Size = ZMatrixRBSizer.GetMinSize()
        Size[0] += 40
        Size[1] = max(Size[1],250) + 20
        ZMatrixRBDisplay.SetSize(Size)
        ZMatrixRB.SetScrollbars(10,10,Size[0]/10-4,Size[1]/10-1)
#        Size[1] = min(Size[1],250)
        G2frame.dataFrame.setSizePosLeft(Size)

    def SetStatusLine(text):
        Status.SetStatusText(text)                                      

    if G2frame.dataDisplay:
        G2frame.dataDisplay.Destroy()
    G2gd.SetDataMenuBar(G2frame,G2frame.dataFrame.RigidBodyMenu)
    G2frame.dataFrame.SetLabel('Rigid bodies')
    if not G2frame.dataFrame.GetStatusBar():
        Status = G2frame.dataFrame.CreateStatusBar()
    SetStatusLine('')

    G2gd.SetDataMenuBar(G2frame,G2frame.dataFrame.RigidBodyMenu)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnAddRigidBody, id=G2gd.wxID_RIGIDBODYADD)    
    G2frame.dataDisplay = G2gd.GSNoteBook(parent=G2frame.dataFrame,size=G2frame.dataFrame.GetClientSize())

    VectorRB = wx.ScrolledWindow(G2frame.dataDisplay)
    G2frame.dataDisplay.AddPage(VectorRB,'Vector rigid bodies')
    ResidueRB = wx.ScrolledWindow(G2frame.dataDisplay)
    G2frame.dataDisplay.AddPage(ResidueRB,'Residue rigid bodies')
    ZMatrix = wx.ScrolledWindow(G2frame.dataDisplay)
    G2frame.dataDisplay.AddPage(ZMatrix,'Z-matrix rigid bodies')
    UpdateVectorRB()
    