import os
import shutil
import subprocess
from kikit import *
from kikit.panelize import Panel
from pcbnewTransition.transition import pcbnew
from pcbnew import *
from kikit.common import fromMm
from shapely.geometry import box

print("starting script ...")

pcbnew.KIID.SeedGenerator(42) # deterministic

scratchFolderDir=os.getcwd()+"/front/scratch"

sourceFilePath=os.getcwd()+"/front/front.kicad_pcb"

outputFilePath=os.getcwd()+"/front/scratch/PANEL.kicad_pcb"

print("clearing scratch folder ...")
# clear scratch folder
if os.path.exists(scratchFolderDir):
    shutil.rmtree(scratchFolderDir)
os.makedirs(scratchFolderDir)

print("separating board into pieces ...")
os.system('kikit separate --source "rectangle; tlx: 33mm; tly: 15mm; brx: 126mm; bry: 71mm" front/front.kicad_pcb front/scratch/front_top.kicad_pcb')
os.system('kikit separate --source "rectangle; tlx: 33mm; tly: 75mm; brx: 125mm; bry: 132mm" front/front.kicad_pcb front/scratch/front_sensor_L.kicad_pcb')
os.system('kikit separate --source "rectangle; tlx: 33mm; tly: 75mm; brx: 125mm; bry: 132mm" front/front.kicad_pcb front/scratch/front_sensor_C.kicad_pcb')
os.system('kikit separate --source "rectangle; tlx: 33mm; tly: 75mm; brx: 125mm; bry: 132mm" front/front.kicad_pcb front/scratch/front_sensor_R.kicad_pcb')
os.system('kikit separate --source "rectangle; tlx: 33mm; tly: 136mm; brx: 125mm; bry: 195mm" front/front.kicad_pcb front/scratch/front_bottom.kicad_pcb') 
os.system('kikit separate --source "rectangle; tlx: 154mm; tly: 43mm; brx: 273mm; bry: 141mm" front/front.kicad_pcb front/scratch/front_back.kicad_pcb')

print("exporting pieces to step ...")
subprocess.run(['kicad-cli', 'pcb', 'export', 'step', 'front/scratch/front_top.kicad_pcb', '-o', 'front/scratch/front_top.step'], stdout=subprocess.DEVNULL)
subprocess.run(['kicad-cli', 'pcb', 'export', 'step', 'front/scratch/front_sensor_C.kicad_pcb', '-o', 'front/scratch/front_sensor.step'], stdout=subprocess.DEVNULL)
subprocess.run(['kicad-cli', 'pcb', 'export', 'step', 'front/scratch/front_bottom.kicad_pcb', '-o', 'front/scratch/front_bottom.step'], stdout=subprocess.DEVNULL)
subprocess.run(['kicad-cli', 'pcb', 'export', 'step', 'front/scratch/front_back.kicad_pcb', '-o', 'front/scratch/front_back.step'], stdout=subprocess.DEVNULL)

print("panelizing ...")

board = LoadBoard(sourceFilePath)

panel = Panel(outputFilePath)

fullPageArea = wxRectMM(0,0,300,200)

destinationLocation = wxPointMM(150-5, 150-25)
panel.appendBoard(os.getcwd()+"/front/scratch/front_top.kicad_pcb", destinationLocation, fullPageArea, inheritDrc=True)

sensorY=150
destinationLocation = wxPointMM(150-20, sensorY)
panel.appendBoard(os.getcwd()+"/front/scratch/front_sensor_L.kicad_pcb", destinationLocation, fullPageArea, inheritDrc=False)

destinationLocation = wxPointMM(150, sensorY)
panel.appendBoard(os.getcwd()+"/front/scratch/front_sensor_C.kicad_pcb", destinationLocation, fullPageArea, inheritDrc=False)

destinationLocation = wxPointMM(150+20, sensorY)
panel.appendBoard(os.getcwd()+"/front/scratch/front_sensor_R.kicad_pcb", destinationLocation, fullPageArea, inheritDrc=False)

destinationLocation = wxPointMM(265, 80)
panel.appendBoard(os.getcwd()+"/front/scratch/front_bottom.kicad_pcb", destinationLocation, fullPageArea, inheritDrc=False, rotationAngle=EDA_ANGLE(90, pcbnew.DEGREES_T))

destinationLocation = wxPointMM(150, 182)
panel.appendBoard(os.getcwd()+"/front/scratch/front_back.kicad_pcb", destinationLocation, fullPageArea, inheritDrc=False)

frame=panel.makeTightFrame(fromMm(4), fromMm(4), fromMm(2.1), fromMm(2.1), fromMm(2.1))

for s in panel.substrates:
    expansion = fromMm(2.2)
    minx, miny, maxx, maxy = s.bounds()
    bbox_box = box(minx-expansion, miny-expansion, maxx+expansion, maxy+expansion)
    s.partitionLine = bbox_box.exterior

# panel.debugRenderPartitionLines()

tabCuts = panel.buildTabsFromAnnotations(fillet=fromMm(0))

# render cuts from lines to mouse bits
panel.makeMouseBites(
    cuts=tabCuts,
    diameter=fromMm(0.3),      # Drill diameter for mouse bites in mm
    spacing=fromMm(0.475),         # Spacing between individual bites in mm
    offset=fromMm(0.0),       # Offset from partition line in mm
    prolongation=fromMm(.6)   # How much to extend the cut in mm
)

panel.addMillFillets(fromMm(1.025))

panel.save()

print("panel saved.")

print("exporting gerbers ...")
subprocess.run(["kicad-cli", "pcb", "export", "gerbers", "--layers", "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts", os.getcwd()+"/front/scratch/PANEL.kicad_pcb", "--output", os.getcwd()+"/front/scratch/gerbers"])
subprocess.run(["kicad-cli", "pcb", "export", "drill", os.getcwd()+"/front/scratch/PANEL.kicad_pcb", "--output", os.getcwd()+"/front/scratch/gerbers"])
subprocess.run(["kicad-cli", "pcb", "export", "dxf", "--output", os.getcwd()+"/front/PCB_Production/panel_F_SolderPasteMask.dxf", "--layers", "F.Paste", "--mode-single", "--output-units", "mm", "--drill-shape-opt", "0", "--common-layers", "", os.getcwd()+"/front/scratch/PANEL.kicad_pcb"])

shutil.make_archive(os.getcwd()+"/front/scratch/gerbers", 'zip', os.getcwd()+"/front/scratch/gerbers")
shutil.rmtree(os.getcwd()+"/front/scratch/gerbers")

shutil.move(os.getcwd()+"/front/scratch/gerbers.zip", os.getcwd()+"/front/PCB_Production/gerbers.zip")

print("done.")