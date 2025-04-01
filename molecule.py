# molecule.py
from drawable import *

from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import DirectButton, DirectFrame, DirectLabel
from direct.task import Task

from panda3d.core import WindowProperties
from panda3d.core import CollisionTraverser, CollisionNode, CollisionHandlerQueue
from panda3d.core import CollisionRay, BitMask32

import copy


class World(ShowBase):

    def __init__(self):
        ShowBase.__init__(self)
        # Click and drag stuff
        self._is_menu_open = False
        self.target = None
        self.dragging = False
        self.start_mouse_pos = None
        self.disableMouse()
        # Change the window title
        props = WindowProperties()
        props.setTitle("mp3.ball")
        self.win.requestProperties(props)

        # Create a button
        self.button = DirectButton(text=("Add"),
                                    scale=0.1,  # Size of the button
                                    pos=(0, 0, -0.975),  # x = 0 (center), y = 0 (default), z = -0.8 (bottom)
                                    command=self.open_menu)
    
        # Set up mouse ray for collision detection
        self.picker = CollisionTraverser()
        self.queue = CollisionHandlerQueue()
        
        self.picker_ray = CollisionRay()
        self.picker_node = CollisionNode("mouse_ray")
        self.picker_node.addSolid(self.picker_ray)
        self.picker_node.setFromCollideMask(BitMask32.bit(1))
        picker_node_path = self.camera.attachNewNode(self.picker_node)
        self.picker.addCollider(picker_node_path, self.queue)
        print("Mouse ray collision node set up.")

        # Accept mouse button clicks
        self.accept("mouse1", self.on_click)  # Left mouse button down
        self.accept("mouse1-up", self.stop_drag)  # Left mouse button up
        print("Waiting for mouse clicks...")
        # Add a task to track mouse pos
        self.taskMgr.add(self.track_mouse_task, "TrackMouseTask")

        # Create atom men
        self.menu_frame = DirectFrame(frameColor=(0, 0, 0, 0.8),
                                    frameSize=(-1, 1, -0.6, 0.6),
                                    pos=(0, 0, 0))
        self._add_button(element = "C", pos=(-0.45, 0, 0))
        self._add_button(element = "H", pos=(-0.15, 0, 0))
        self._add_button(element = "O", pos=(0.15, 0, 0))
        self._add_button(element = "F", pos=(0.45, 0, 0))
 
        self.menu_frame.hide()
    def set_molecule(self, molecule):
        self._molecule = molecule

    def on_click(self):
        if self.mouseWatcherNode.hasMouse():

            # Update ray to match mouse pos
            mouse_pos = self.mouseWatcherNode.getMouse()
            self.picker_ray.setFromLens(self.camNode, mouse_pos.getX(),
                                        mouse_pos.getY())
            print(f"Mouse pos: {mouse_pos}")

            # Traverse for collisions
            self.picker.traverse(self.render)
            
            if self.queue.getNumEntries() > 0:
                self.queue.sortEntries()
                entry = self.queue.getEntry(0)  # Closest hit
                collidee = entry.getIntoNodePath()
                if self.target != None:
                    atom2 = collidee.getPythonTag("owner")
                    if atom2 != self.target:
                        if not self._molecule.try_delete_bond(self.target, atom2):
                            self.add_bond(self.target, atom2)
                            return
                        else:
                            self._molecule.update()
                            print("deleted bond")
                            return
                self.target = collidee.getPythonTag("owner")
                print("Clicked on " + str(self.target.atom_id))
                self.start_drag()
            else:
                self.target = None

    def add_bond(self,atom1,atom2):
        self._molecule.add_bond(atom1,atom2)
        self._molecule.update()

    def open_menu(self):
        if not self._is_menu_open:
            self._is_menu_open=True
            self.menu_frame.show()

    def start_drag(self):
        if self.mouseWatcherNode.hasMouse():
            self.dragging = True
            self.start_mouse_pos = copy.deepcopy(self.mouseWatcherNode.getMouse())

    def stop_drag(self):
        self.dragging = False

    def track_mouse_task(self, task):
        if self.mouseWatcherNode.hasMouse() and self.dragging\
            and self.start_mouse_pos and self.target != None:
            # Debugging: Current pos and distance
            (x, y) = self._get_drag_distance()
            self.target.move(LVecBase3f(10*x, 0.0, 10*y))
            self.start_mouse_pos = copy.deepcopy(self.mouseWatcherNode.getMouse())
            self._molecule.update()
        return task.cont  # Continue the task on the next frame

    def add_atom(self,element):
        self.menu_frame.hide()  # Hides the menu frame and its children
        self._is_menu_open=False
        atom = self._molecule.add_atom(element)
        print(atom.model.getPos())

    def _add_button(self, element, pos):
        DirectButton(text="add " + element,
                    scale=0.08,
                    pos=pos,
                    command=self.add_atom,
                    extraArgs=[element],
                    parent=self.menu_frame)

    def _get_drag_distance(self):
        if self.start_mouse_pos:
            # Calculate the drag distance
            current_mouse_pos = self.mouseWatcherNode.getMouse()
            drag_x = current_mouse_pos.getX() - self.start_mouse_pos.getX()
            drag_y = current_mouse_pos.getY() - self.start_mouse_pos.getY()
            return (drag_x, drag_y)
        return (0.0, 0.0)

# Example usage
if __name__ == "__main__":
    world = World()
    molecule = Molecule(world)
    world.set_molecule(molecule)
    #world.camera.lookAt(molecule.atoms[-1]._model)     # Point the camera at the model

    world.run()
