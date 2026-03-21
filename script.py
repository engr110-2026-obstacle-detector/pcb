import os
import shutil
import subprocess
from kikit import *
from kikit.panelize import Panel
from pcbnewTransition.transition import pcbnew
from pcbnew import *
from kikit.common import fromMm
from shapely.geometry import box

def makeGerbers(inName, outName):
    subprocess.run(["kicad-cli", "pcb", "export", "gerbers", "--layers", "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts", os.getcwd()+"/front/scratch/"+inName, "--output", os.getcwd()+"/front/scratch/"+outName])
    subprocess.run(["kicad-cli", "pcb", "export", "drill", os.getcwd()+"/front/scratch/"+inName, "--output", os.getcwd()+"/front/scratch/"+outName])

    shutil.make_archive(os.getcwd()+"/front/scratch/"+outName, 'zip', os.getcwd()+"/front/scratch/"+outName)
    shutil.rmtree(os.getcwd()+"/front/scratch/"+outName)

    shutil.move(os.getcwd()+"/front/scratch/"+outName+".zip", os.getcwd()+"/front/PCB_Production/"+outName+".zip")

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
os.system('kikit separate --source "rectangle; tlx: 154mm; tly: 43mm; brx: 273mm; bry: 141mm" front/front.kicad_pcb front/scratch/front_back.kicad_pcb')

print("exporting pieces to 3d models ...")
subprocess.run(['kicad-cli', 'pcb', 'export', 'step', 'front/scratch/front_top.kicad_pcb', '-o', 'front/3d_models/front_top.step'], stdout=subprocess.DEVNULL)
subprocess.run(['kicad-cli', 'pcb', 'export', 'step', 'front/scratch/front_sensor_C.kicad_pcb', '-o', 'front/3d_models/front_sensor.step'], stdout=subprocess.DEVNULL)
subprocess.run(['kicad-cli', 'pcb', 'export', 'step', 'front/scratch/front_back.kicad_pcb', '-o', 'front/3d_models/front_back.step'], stdout=subprocess.DEVNULL)

subprocess.run(['kicad-cli', 'pcb', 'export', 'stl', 'front/scratch/front_top.kicad_pcb', '-o', 'front/3d_models/front_top.stl'], stdout=subprocess.DEVNULL)
subprocess.run(['kicad-cli', 'pcb', 'export', 'stl', 'front/scratch/front_sensor_C.kicad_pcb', '-o', 'front/3d_models/front_sensor.stl'], stdout=subprocess.DEVNULL)
subprocess.run(['kicad-cli', 'pcb', 'export', 'stl', 'front/scratch/front_back.kicad_pcb', '-o', 'front/3d_models/front_back.stl'], stdout=subprocess.DEVNULL)

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

destinationLocation = wxPointMM(150, 182)
panel.appendBoard(os.getcwd()+"/front/scratch/front_back.kicad_pcb", destinationLocation, fullPageArea, inheritDrc=False)

panel.save()

print("panel saved.")

subprocess.run(['kicad-cli', 'pcb', 'export', 'stl', '--board-only', 'front/scratch/PANEL.kicad_pcb', '-o', 'front/3d_models/stencil.stl'], stdout=subprocess.DEVNULL)
subprocess.run(['kicad-cli', 'pcb', 'export', 'step', '--board-only', 'front/scratch/PANEL.kicad_pcb', '-o', 'front/3d_models/stencil.step'], stdout=subprocess.DEVNULL)

print("exporting gerbers ...")
makeGerbers("PANEL.kicad_pcb", "stencil_gerbers")
makeGerbers("front_top.kicad_pcb", "front_top_gerbers")
makeGerbers("front_sensor_C.kicad_pcb", "front_sensor_gerbers")
makeGerbers("front_back.kicad_pcb", "front_back_gerbers")

print("rendering images ...")
subprocess.run(["kicad-cli", "pcb", "render", os.getcwd()+"/front/scratch/PANEL.kicad_pcb", "--output", os.getcwd()+"/front/renders/panel.png"])

subprocess.run(["kicad-cli", "pcb", "render", os.getcwd()+"/front/scratch/front_top.kicad_pcb", "--output", os.getcwd()+"/front/renders/front_top.png"])
subprocess.run(["kicad-cli", "pcb", "render", os.getcwd()+"/front/scratch/front_sensor_C.kicad_pcb", "--output", os.getcwd()+"/front/renders/front_sensor_C.png"])
subprocess.run(["kicad-cli", "pcb", "render", os.getcwd()+"/front/scratch/front_back.kicad_pcb", "--output", os.getcwd()+"/front/renders/front_back.png"])


print("done.")
