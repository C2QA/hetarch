from HarchSim.StandardCell.DistillationCell import DistillationCell

class DistillationModule:
    def __init__(self,
                 distillation_cells : list[DistillationCell]):
        self.distillation_cells = distillation_cells
        self.clock = None
        self.locked_cells = {}

    def find_available_cell(self):
        for cell in self.distillation_cells:
            if cell.is_available():
                return cell
        return None

    def is_cell_available(self):
        for cell in self.distillation_cells:
            if cell.is_available():
                return True
        return False

    def get_available_cell(self):
        for cell in self.distillation_cells:
            if cell.is_available():
                valid_cell = cell
                break
        self.locked_cells[valid_cell] = {}
        self.locked_cells[valid_cell]["time"] = self.clock.clock
        self.locked_cells[valid_cell]["compute_time"] = 500e-9
        self.distillation_cells.remove(valid_cell)
        return valid_cell

    def bind_clock_to_modules(self):
        for module in self.distillation_cells:
            module.clock = self.clock

    def check_unlock(self):
        keys = list(self.locked_cells.keys())
        for key in keys:
            if self.clock.clock - self.locked_cells[key]["time"] > self.locked_cells[key]["compute_time"]:
                self.distillation_cells.append(key)
                self.locked_cells.pop(key)

    def input(self,qb1,qb2):
        cell = self.find_available_cell()
        if cell is not None:
            cell.input(qb1,qb2)
            return True
        return False

    def output(self):
        for cell in self.distillation_cells:
            if cell.PENDING:
                dm = cell.output()
                cell.set_available()
                return dm, True
        return None, False


