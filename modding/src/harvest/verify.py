"""Execute the built x86 dispatch and existing resource checks with stubbed game services."""

from collections import defaultdict
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
root = ROOT / "build" / "harvest"
POWER_ENTRY = 0x897EE4
POWER_END = 0x897F25
TREE_MODE = 0xF4F395
RESOURCE_FILTER = 0xF4F0B9
SUPPLY_MANAGER = 0xA000
WORKER = 0x1000
AI = 0x2000
WORKER_DATA = 0x3000
TARGET = 0x4000
TEMPLATE = 0x5000
FRAME = 0x9000
STACK = FRAME - 0x20


def disassemble(executable):
    instructions = {}
    for low, high in ((POWER_ENTRY, POWER_END), (0xF4F035, 0xF4F100), (TREE_MODE, 0xF4F3C4), (0xF4F770, 0xF4F7B5)):
        output = subprocess.check_output([
            "objdump", "-d", "-Mintel", "--insn-width=16",
            f"--start-address={low}", f"--stop-address={high}", str(executable)
        ], text=True)
        for line in output.splitlines():
            match = re.match(r"\s*([0-9a-f]+):\s+((?:[0-9a-f]{2} )+)\s+(\w+)\s*(.*?)$", line)
            if match:
                address, encoded, operation, args = match.groups()
                address = int(address, 16)
                argument_list = args.split(",") if args else []
                instructions[address] = (address + len(encoded.split()), operation, argument_list)
    return instructions


class CPU:
    def __init__(self, executable):
        self.instructions = disassemble(executable)
        self.register = dict.fromkeys(("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp"), 0)
        self.memory = defaultdict(int)
        self.zero = False
        self.calls = []
        self.nearest_supply = TARGET

    def get_memory(self, address, width=4):
        return sum(self.memory[address + offset] << (8 * offset) for offset in range(width))

    def set_memory(self, address, value, width=4):
        for offset in range(width):
            self.memory[address + offset] = (value >> (8 * offset)) & 255

    def address(self, operand):
        expression = operand[operand.index("[") + 1:operand.index("]")]
        for key, value in self.register.items():
            expression = expression.replace(key, str(value))
        assert re.fullmatch(r"[a-f0-9x+*-]+", expression)
        return eval(expression, {"__builtins__": {}})

    def get(self, operand):
        if operand in self.register:
            return self.register[operand]
        if operand in ("al", "bl", "cl", "dl"):
            return self.register[f"e{operand[0]}x"] & 255
        if "[" in operand:
            return self.get_memory(self.address(operand), 1 if operand.startswith("BYTE") else 4)
        return int(operand, 16)

    def put(self, operand, value):
        if operand in self.register:
            self.register[operand] = value & 0xFFFFFFFF
        elif operand in ("al", "bl", "cl", "dl"):
            reg = f"e{operand[0]}x"
            self.register[reg] = (self.register[reg] & ~255) | (value & 255)
        else:
            assert "[" in operand, operand
            self.set_memory(self.address(operand), value, 1 if operand.startswith("BYTE") else 4)

    def push(self, value):
        self.register["esp"] -= 4
        self.set_memory(self.register["esp"], value)

    def pop(self):
        value = self.get_memory(self.register["esp"])
        self.register["esp"] += 4
        return value

    def stub(self, address):
        self.calls.append(address)
        esp, ecx = self.register["esp"], self.register["ecx"]
        first, second = self.get_memory(esp), self.get_memory(esp + 4)
        if address == 0x8FA834:  # Engine tree search, which requires tree mode.
            assert (ecx, first, second) == (SUPPLY_MANAGER, WORKER, FRAME - 0x20)
            self.register["ecx"] = AI + 0x4AC
            self.push(0)
            self.run(TREE_MODE, 0)
            self.register["esp"] += 8
        elif address == 0x8FAA51:
            assert (ecx, first) == (SUPPLY_MANAGER, WORKER)
            self.register["eax"] = self.nearest_supply
            self.register["esp"] += 4
        elif address == 0x66C609:
            assert (ecx, first, second) == (AI + 0x20, TARGET, 2)
            self.register["esp"] += 8
        elif address == 0x771655:
            assert (ecx, first, second) == (AI + 0x20, FRAME - 0x20, 2)
            self.register["esp"] += 8
        else:
            raise AssertionError(hex(address))

    def run(self, address, stop):
        for _ in range(500):
            if address == stop:
                return
            following, operation, args = self.instructions[address]
            if operation in ("mov", "movzx"):
                self.put(args[0], self.get(args[1]))
            elif operation == "lea":
                self.put(args[0], self.address(args[1]))
            elif operation == "push":
                self.push(self.get(args[0]))
            elif operation == "pop":
                self.put(args[0], self.pop())
            elif operation == "leave":
                self.register["esp"] = self.register["ebp"]
                self.register["ebp"] = self.pop()
            elif operation == "ret":
                following = self.pop()
            elif operation == "call":
                dest = self.get(args[0])
                if dest in self.instructions:
                    self.push(following)
                    following = dest
                else:
                    self.stub(dest)
            elif operation in ("je", "jne", "jmp"):
                if operation == "jmp" or self.zero == (operation == "je"):
                    following = self.get(args[0])
            elif operation in ("sete", "setne"):
                self.put(args[0], int(self.zero == (operation == "sete")))
            elif operation in ("cmp", "test"):
                one, two = map(self.get, args)
                self.zero = (one == two) if operation == "cmp" else (one & two == 0)
            elif operation in ("add", "sub", "xor", "or", "and", "inc"):
                one = self.get(args[0])
                two = self.get(args[1]) if len(args) == 2 else 1
                value = {"add": one + two, "sub": one - two, "xor": one ^ two,
                         "or": one | two, "and": one & two, "inc": one + 1}[operation]
                self.put(args[0], value)
                self.zero = self.get(args[0]) == 0
            else:
                raise AssertionError((hex(address), operation, args))
            address = following
        raise AssertionError("instruction limit exceeded")

    def ability(self, *, trees=0, mask=1, valid_worker=True, has_stone=True):
        self.calls.clear()
        self.nearest_supply = TARGET if has_stone else 0
        self.register.update(ebp=FRAME, esp=STACK, edi=WORKER, ebx=AI, ecx=SUPPLY_MANAGER)
        self.set_memory(WORKER + 0x260, AI)
        self.set_memory(AI + 4, WORKER_DATA)
        self.set_memory(WORKER_DATA, 0xC086D8 if valid_worker else 0)
        self.set_memory(WORKER_DATA + 0x80, trees, 1)
        self.set_memory(WORKER_DATA + 0xB0, mask)
        self.set_memory(AI + 0x3CC, 1, 1)
        self.run(POWER_ENTRY, POWER_END)
        assert tuple(self.register[v] for v in ("esp", "ebp", "edi", "ebx")) == (STACK, FRAME, WORKER, AI)
        return self.calls.copy(), self.get_memory(AI + 0x3CC, 1)

    def filter(self, *, center, target_mask, tree_flag=False):
        self.register.update(eax=WORKER_DATA + 0x94, edx=TARGET, ecx=center, esp=STACK)
        self.set_memory(TARGET + 4, TEMPLATE)
        self.set_memory(TEMPLATE + 0x650, target_mask)
        self.set_memory(TEMPLATE + 0x113, 0x40 if tree_flag else 0, 1)
        self.set_memory(WORKER_DATA + 0xB0, 1)
        self.set_memory(WORKER_DATA + 0xD0, 16)
        self.push(0)
        self.run(RESOURCE_FILTER, 0)
        assert self.register["esp"] == STACK
        return self.register["eax"]


before = CPU(ROOT / "inputs" / "game.dat")
after = CPU(root / "game.dat")
assert before.ability() == ([0x8FA834], 1)
assert after.ability() == ([0x8FAA51, 0x66C609], 0)
assert after.ability(has_stone=False) == ([0x8FAA51], 1)
assert before.ability(trees=1, mask=0) == after.ability(trees=1, mask=0) == ([0x8FA834, 0x771655], 0)
assert after.ability(mask=0) == ([0x8FA834], 1)
assert after.ability(valid_worker=False) == ([0x8FA834], 1)
assert after.filter(center=0, target_mask=1) == 1
assert after.filter(center=0, target_mask=0, tree_flag=True) == 0
assert after.filter(center=1, target_mask=16) == 1
assert after.filter(center=1, target_mask=0) == 0
print("Verified original no-op, stone order, empty search, existing tree order, and stone/supply center filters.")
