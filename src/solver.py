from __future__ import print_function
from ortools.sat.python import cp_model
from pprint import pprint

class ResidentsPartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, shifts, num_residents, num_days, sols):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._shifts = shifts
        self._num_residents = num_residents
        self._num_days = num_days
        self._solutions = set(sols)
        self._solution_count = 0

    def on_solution_callback(self):
        if self._solution_count in self._solutions:
            print('Solution %i' % self._solution_count)
            for d in range(self._num_days):
                print('Day %i' % d)
                for n in range(self._num_residents):
                    is_working = False
                    if self.Value(self._shifts[(n, d)]):
                        is_working = True
                        print('  Resident %i works day %i' % (n, d))
                    if not is_working:
                        print('  Resident {} does not work'.format(n))
            print()
        self._solution_count += 1

    def solution_count(self):
        return self._solution_count

def main():

    num_residents = 6
    num_days = 30
#   num_weekdays = 7
    all_residents = range(num_residents)
    all_days = range(num_days)
#   all_weekdays = range(num_weekdays)
#   friday_sunday = True
    resident_0_off = [1, 14, 7, 23]
    resident_1_off = [3, 14, 18, 20]
    resident_2_off = [8, 10, 18, 29]
    resident_3_off = [1, 8, 12, 25]
    resident_4_off = [5, 6, 7, 8]
    resident_5_off = [3, 8, 12, 20]
#   workers_per_weekday = [2, 1, 2, 2, 2, 1, 2]

    # create Model
    model = cp_model.CpModel()

    # Creates shift variables.
    # shifts[(r, d)]: resident 'r' works on day 'd'.
    shifts = {}
    for r in all_residents:
        for d in all_days:
            shifts[(r, d)] = model.NewBoolVar('shift_r%id%i' % (r, d))
    
    # pprint(shifts)

    # Each shift is assigned to exactly one resident in the schedule period.
    for d in all_days:
            model.Add((sum(shifts[(r, d)] for r in all_residents) == 1 ) or (sum(shifts[(r, d)] for r in all_residents) == 2 ))
    

    # min_shifts_per_resident is the largest integer such that every resident
    # can be assigned at least that many shifts. If the number of residents doesn't
    # divide the total number of shifts over the schedule period,
    # some residents have to work one more shift, for a total of
    # resident + 1.
    min_shifts_per_resident = 4
    max_shifts_per_resident = 8
    for r in all_residents:
        num_shifts_worked = sum(
            shifts[(r, d)] for d in all_days)
        model.Add(min_shifts_per_resident <= num_shifts_worked)
        model.Add(num_shifts_worked <= max_shifts_per_resident)

    # Add constraints for resident free days
    for o in resident_0_off:
        model.Add(shifts[(0, o)] == 0)
    for o in resident_1_off:
        model.Add(shifts[(1, o)] == 0)
    for o in resident_2_off:
        model.Add(shifts[(2, o)] == 0)
    for o in resident_3_off:
        model.Add(shifts[(3, o)] == 0)
    for o in resident_4_off:
        model.Add(shifts[(4, o)] == 0)
    for o in resident_5_off:
        model.Add(shifts[(5, o)] == 0)

    # Adds constraint to prevent residents from working two consecutive days
    for r in all_residents:
        for d in all_days:
            if d < 29:
                next_day = d+1
                model.Add(
                    (shifts[(r, d)] + shifts[(r, next_day)]) <= 1
                )

    # Creates the solver and solve.
    solver = cp_model.CpSolver()
    solver.parameters.linearization_level = 0

    # Display the first five solutions.
    a_few_solutions = range(5)
    solution_printer = ResidentsPartialSolutionPrinter(shifts, num_residents,
                                                    num_days, a_few_solutions)

    solver.SearchForAllSolutions(model, solution_printer)

    # Statistics.
    print()
    print('Statistics')
    print('  - conflicts       : %i' % solver.NumConflicts())
    print('  - branches        : %i' % solver.NumBranches())
    print('  - wall time       : %f s' % solver.WallTime())
    print('  - solutions found : %i' % solution_printer.solution_count())


if __name__ == '__main__':
    main()