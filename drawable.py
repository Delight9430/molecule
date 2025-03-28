

from panda3d.core import Point3, LVecBase3f, LVecBase3f, LVecBase4f
from panda3d.core import CollisionNode, CollisionSphere, BitMask32

from math import atan2, degrees
import copy

class Drawable:
    def __init__(self, world, file_name,
                 pos = LVecBase3f(0.0, 20.0, 0.0), 
                 color = LVecBase4f(1, 0, 0, 1), size = 2.5, scale = 1):
        self._file_name = file_name
        # This is redundant, should use getter
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
        self.pos = self.model.getPos()

    def draw(self):
        self.model.reparentTo(self._world.render)
        self.model.setPos(self.pos)
        self.model.setColor(self._color)
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
        # We have to start backed away from the camera
        self.pos = LVecBase3f(0, 30, 0)

    def center(self):
        pass

    def add_atom(self, element):
        atom_pos = copy.deepcopy(self.pos)
        print(f"added atom at {atom_pos}")
        new_atom = Atom(element, self.atom_count, self._world, atom_pos) 
                       
        self.atoms.append(new_atom)

        self.atom_count += 1
        return new_atom
    
    def add_bond(self, left, right):
        new_bond = Bond(self._world, 
                        copy.deepcopy(self.pos),left,right)
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