# molecule.py
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from math import pi, atan2, degrees
import copy
from panda3d.core import WindowProperties, LVecBase3f, LVecBase4f
from panda3d.core import CollisionTraverser, CollisionNode, CollisionHandlerQueue
from panda3d.core import CollisionRay, CollisionSphere, BitMask32
from panda3d.core import Point3, LVecBase3f
from direct.gui.DirectGui import DirectButton

class Drawable:
    def __init__(self, world, file_name,
                 pos = LVecBase3f(0.0, 20.0, 0.0), 
                 color = LVecBase4f(1, 0, 0, 1), size = 2.5, scale = 1):
        self._file_name = file_name
        self.pos = pos
        self._color = color
        self._world = world
        self.size = LVecBase3f(size, size, size)
        self.scale = LVecBase3f(scale, scale, scale)
        self.model = self._world.loader.loadModel(self._file_name)

    def get_end(self):
        #TODO: take into acount the shape
        end = copy.deepcopy(self.pos)
        end.x += self.size.x
        return end

    def move(self, distance):
        self.model.setPos(self.model.getPos() + distance)

    def draw(self):
        self.model.reparentTo(self._world.render)
        self.model.setPos(self.pos)  # Position the second ball to the right
        self.model.setColor(self._color)  # Set the color to orange (RGBA)
        self.model.setScale(self.scale)
        #self._model.ls()

    def update(self):
        pass

class Bond(Drawable):
    def __init__(self, world, pos, left , right):
        super().__init__(world, "./stick.egg", pos,
                         LVecBase4f(1, 1, 1, 1), size = 2.5, scale = 2)
        # Rotate the bond
        self.model.setHpr(0, 0, 90)
        self._left = left
        self._right = right

    def update(self):
        distance = self._left.model.getDistance(self._right.model)
        newScale=copy.deepcopy(self.scale)
        newScale.z=distance/2
        self.model.setScale(newScale)
        diffVector = self._left.model.getPos() - self._right.model.getPos()
        angle = atan2(diffVector.getX(), diffVector.getZ())
        angle_degrees = degrees(angle)
        self.model.setHpr(0, 0, angle_degrees)
        
        # Calculate the mid-point
        mid_point = (self._left.model.getPos() + self._right.model.getPos()) / 2
        # Set model at the mid-point
        self.model.setPos(mid_point)

class Atom(Drawable):
    def __init__(self, element, atom_id, world, pos):
        if element == "H":
            color = LVecBase4f(1, 1, 1, 1)
        elif element == "O":
            color = LVecBase4f(1, 0, 0, 1)
        elif element == "C":
            color = LVecBase4f(0, 0, 0, 1)
        super().__init__(world, "models/misc/sphere.egg", pos, color)
        self.element = element
        self.atom_id = atom_id
        # Add collision detecti,on to the model
        collision_node = CollisionNode("model_collision")
        collision_node.addSolid(CollisionSphere(Point3(0, 0, 0), 1))  # Adjust size
        collision_node.setIntoCollideMask(BitMask32.bit(1))
        collision_node_path = self.model.attachNewNode(collision_node)
        collision_node_path.setPythonTag("owner", self)
    
class Molecule:
    def __init__(self, world):
        self.atoms = []
        self.bonds = []
        self.atom_count = 0
        self._world = world
        # We have to start 20 away from the camera
        self._start_pos = LVecBase3f(-5, 30, 0)
        self._end_pos = self._start_pos

    def center(self):
        pass

    def add_atom(self, element, attached_to_id=None, dX = 0.0, angle = 0):
        atom_pos = copy.deepcopy(self._end_pos)
        atom_pos.z = atom_pos.z+dX
        new_atom = Atom(element, self.atom_count, self._world,atom_pos) 
                       
        self._end_pos = new_atom.get_end()
        self.atoms.append(new_atom)

        if attached_to_id is not None:
            attached_to_atom = self.get_atom_by_id(attached_to_id)
            if attached_to_atom:
                attached_to_atom.bonds.append(new_atom.atom_id)
                new_atom.bonds.append(attached_to_atom.atom_id)
            else:
                print(f"No atom found with ID {attached_to_id}")

        self.atom_count += 1
        return new_atom
    
    def add_bond(self, left,right):
        new_bond = Bond(self._world, 
                        copy.deepcopy(self._end_pos),left,right)
        self._end_pos = new_bond.get_end()
        print(self._end_pos)
        self.bonds.append(new_bond)

    def draw(self):
        for bond in self.bonds:
            bond.draw()
        for atom in self.atoms:
            atom.draw()

    def update(self):
        for atom in self.atoms:
            atom.update()
        for bond in self.bonds:
            bond.update()

    def get_atom_by_id(self, atom_id):
        for atom in self.atoms:
            if atom.atom_id == atom_id:
                return atom
        return None

class World(ShowBase):

    def __init__(self):
        ShowBase.__init__(self)
        # Click and drag stuff
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
                                    command=self.add_atom)
    
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
                print("Collision detected")
                self.queue.sortEntries()
                entry = self.queue.getEntry(0)  # Closest hit
                collidee = entry.getIntoNodePath()
                self.target = collidee.getPythonTag("owner")
                print("collided with " + str(self.target.atom_id))
                self.start_drag()
                #self.move_panda(Point3(0,5,0))

    def start_drag(self):
        if self.mouseWatcherNode.hasMouse():
            self.dragging = True
            self.start_mouse_pos = copy.deepcopy(self.mouseWatcherNode.getMouse())

    def stop_drag(self):
        self.dragging = False
        self.target = None

    def _get_drag_distance(self):
        if self.start_mouse_pos:
            # Calculate the drag distance
            current_mouse_pos = self.mouseWatcherNode.getMouse()
            drag_x = current_mouse_pos.getX() - self.start_mouse_pos.getX()
            drag_y = current_mouse_pos.getY() - self.start_mouse_pos.getY()
            return (drag_x, drag_y)
        return (0.0, 0.0)

    def track_mouse_task(self, task):
        if self.mouseWatcherNode.hasMouse() and self.dragging\
            and self.start_mouse_pos and self.target != None:
            # Debugging: Current pos and distance
            (x, y) = self._get_drag_distance()
            self.target.move(LVecBase3f(10*x, 0.0, 10*y))
            self.start_mouse_pos = copy.deepcopy(self.mouseWatcherNode.getMouse())
            self._molecule.update()
        return task.cont  # Continue the task on the next frame

    def add_atom(self):
        molecule = Molecule(world)
        molecule.add_atom("C")
        molecule.draw()
        molecule.update()
        self.set_molecule(molecule)



# Example usage
if __name__ == "__main__":
    world = World()
    molecule = Molecule(world)

    h1 = molecule.add_atom("H")
    h2 = molecule.add_atom("H")
    c1 = molecule.add_atom("C")
    c2 = molecule.add_atom("C")
    h3 = molecule.add_atom("H")
    h4 = molecule.add_atom("H")
    molecule.add_bond(h1, c1)
    molecule.add_bond(h2, c1)
    molecule.add_bond(c1, c2)
    molecule.add_bond(h3, c2)
    molecule.add_bond(h4, c2)
    molecule.draw()
    molecule.update()
    world.set_molecule(molecule)
    #world.camera.lookAt(molecule.atoms[-1]._model)     # Point the camera at the model

    world.run()
