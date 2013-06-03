'''
*ImageCalibrants: Calibration Standards*
----------------------------------------

GSASII powder calibrants as a dictionary of substances commonly used for powder
calibrations for image data.

'''
#GSASII powder calibrants file; dictionary of substances commonly used for powder
#calibrations. Each entry consists of:
# 'name':(Bravais no,(a,b,c,alpha,beta,gamma),no. lines skipped,(dmin,pixLimit,cutOff)
#Useful Bravais nos.: F-cubic=0,I-cubic=1,P-cubic=2,R3/m(hex)=3, P6=4, P4mmm=6
Calibrants={
'':([0,],[(0,0,0,0,0,0),],0,(0,0,0)),
'LaB6  SRM660a':([2,],[(4.1569162,4.1569162,4.1569162,90,90,90),],0,(1.0,10,10)),
'LaB6  SRM660a skip 1':([2,],[(4.1569162,4.1569162,4.1569162,90,90,90),],1,(1.0,10,10)),
'LaB6  SRM660': ([2,],[(4.15695,4.15695,4.15695,90,90,90),],0,(1.0,10,10)),
'Si    SRM640c':([0,],[(5.4311946,5.4311946,5.4311946,90,90,90),],0,(1.,10,10)),
'CeO2  SRM674b':([0,],[(5.411651,5.411651,5.411651,90,90,90),],0,(1.0,2,1)),
'Al2O3 SRM676a':([3,],[(4.759091,4.759091,12.991779,90,90,120),],0,(1.0,5,5)),
'Ni   @ 298K':([0,],[(3.52475,3.52475,3.52475,90,90,90),],0,(1.0,10,10)),
'NaCl @ 298K':([0,],[(5.6402,5.6402,5.6402,90,90,90),],0,(1.0,10,10)),
'NaCl even hkl only':([2,],[(2.8201,2.8201,2.8201,90,90,90),],0,(1.0,10,10)),
'Ag behenate':([6,],[(1.0,1.0,58.380,90,90,90),],0,(7.0,5,1)),
'Spun Si 3600 line/mm grating':([6,],[(1.0,1.0,2777.78,90,90,90),],2,(200.,5,1)),
'Spun Si 7200 line/mm grating':([6,],[(1.0,1.0,1388.89,90,90,90),],1,(200.,5,1)),
'Pt   @ 298K':([0,],[(3.9231,3.9231,3.9231,90,90,90),],0,(1.0,5,1)),
'LaB6 & CeO2':([2,0],[(4.1569162,4.1569162,4.1569162,90,90,90),(5.411651,5.411651,5.411651,90,90,90)],0,(1.0,2,1)),
}
    
