

from panda3d.core import Point3, LVecBase3f, LVecBase3f, LVecBase4f
from panda3d.core import CollisionNode, CollisionSphere, BitMask32

from math import atan2, degrees, sqrt
import copy

class Drawable:
    def __init__(self, world, file_name,
                 pos = LVecBase3f(0.0, 20.0, 0.0), 
                 color = LVecBase4f(1, 0, 0, 1), scale = 1):
        self._file_name = file_name
        # This is redundant, should use getter
        self.pos = pos
        self._color = color
        self._world = world
        self.scale = LVecBase3f(scale, scale, scale)
        self.model = self._world.loader.loadModel(self._file_name)

        self.model.reparentTo(self._world.render)
        self.model.setPos(self.pos)
        self.model.setColor(self._color)
        self.model.setScale(self.scale)

    def __del__(self):
        self.model.removeNode()

    def move(self, distance):
        self.model.setPos(self.model.getPos() + distance)
        self.pos = self.model.getPos()

    def get_distance(self, other):
        pos1 = self.model.getPos()
        pos2 = other.model.getPos()

        dx = pos2.getX() - pos1.getX()
        dy = pos2.getY() - pos1.getY()
        dz = pos2.getZ() - pos1.getZ()

        distance = sqrt(dx**2 + dy**2 + dz**2)
        return distance

    def update(self):
        pass

class Bond(Drawable):
    def __init__(self, world, pos, left, right):
        super().__init__(world, "./stick.egg", pos,
                         LVecBase4f(1, 1, 1, 1), scale = 2)
        # Rotate the bond
        self.model.setHpr(0, 0, 90)
        self._left = left
        self._right = right

    def has_atoms(self, first, second):
        have_first=False
        have_second=False
        if first ==self._left:
            have_first=True
        elif first==self._right:
            have_first=True

        if second ==self._right:
            have_second=True
        elif second ==self._left:
            have_second=True
        return have_first and have_second


    def update(self):
        print(f"left: {self._left.model.getPos()}, right {self._right.model.getPos()}")
        distance = self._left.get_distance(self._right)
        print(f"distance: {distance}")
        newScale=copy.deepcopy(self.scale)
        newScale.z=distance/2
        print(f"scale: {newScale.z}")
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
            size = 0.75
        elif element == "O":
            color = LVecBase4f(1, 0, 0, 1)
            size = 1.0
        elif element == "C":
            color = LVecBase4f(0, 0, 0, 1)
            size = 1.0
        elif element == "F":
            color = LVecBase4f(1.0, 0.5, 0.0, 1.0)
            size = 0.75
        elif element == "Cl":
            color = LVecBase4f(0.0862, 0.6627, 0.2745, 1.0)
            size = 1.0
        elif element == "S":
            color = LVecBase4f(1.0, 0.9490196078, 0.00000000000000, 1.0)
            size = 1.0
        super().__init__(world, "models/misc/sphere.egg", pos, color, size)
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

    def try_delete_bond(self, left, right):
        for bond in self.bonds:
            if bond.has_atoms(left, right):
                self.bonds.remove(bond)
                return True
        return False

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