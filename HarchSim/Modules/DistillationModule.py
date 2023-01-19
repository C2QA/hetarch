from HarchSim.StandardCell.DistillationCell import DistillationCell

class DistillationModule:
    def __init__(self,
                 distillation_cells : list[DistillationCell]):
        self.distillation_cells = distillation_cells
        self.clock = None

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

    def bind_clock_to_modules(self):
        for module in self.distillation_cells:
            module.clock = self.clock

    def input(self,qb1,qb2):
        cell = self.find_available_cell()
        if cell is not None:
            cell.input(qb1,qb2)
            cell.set_not_available()
            return True
        return False

    def output(self):
        for cell in self.distillation_cells:
            if cell.PENDING:
                dm = cell.output()
                cell.set_available()
                return dm, True
        return None, False


