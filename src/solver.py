from __future__ import print_function
from ortools.sat.python import cp_model
from pprint import pprint

class ResidentsPartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, shifts, num_residents, num_days, sols, weekday_names, weekday_calendar, limit):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._shifts = shifts
        self._num_residents = num_residents
        self._num_days = num_days
        self._solutions = set(sols)
        self._solution_count = 0
        self._weekday_names = weekday_names
        self._weekday_calendar = weekday_calendar
        self._solution_limit = limit

    def on_solution_callback(self):
        if self._solution_count in self._solutions:
            print(f"Solution {self._solution_count + 1}")
            for d in range(self._num_days):
                print(f"Day {d+1} - {self._weekday_names[self._weekday_calendar[d]]}")
                for n in range(self._num_residents):
                    is_working = False
                    if self.Value(self._shifts[(n, d)]):
                        is_working = True
                        print('  Resident %i works day %i' % (n, d+1))
                    if not is_working:
                        print('  Resident {} does not work'.format(n))
            print()
        if self._solution_count + 1 >= self._solution_limit:
            print(f"Solution search limit number reached after {self._solution_count + 1}. Stopping search.")
            self.StopSearch()
        else:
            self._solution_count += 1

    def solution_count(self):
        return self._solution_count

def main():

    num_residents = 6
    num_days = 30
    all_residents = range(num_residents)
    all_days = range(num_days)
    friday_sunday = True
#   Esta variable define que cae el primer dia del mes
    first_week_day = 3 #Jueves
    calendar_weekdays = _assign_weekdays(first_week_day, all_days)
    weekday_names = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday"
    ]

    resident_0_off = [1, 14, 7, 23]
    resident_1_off = [3, 14, 18, 20]
    resident_2_off = [8, 10, 18, 29]
    resident_3_off = [1, 8, 12, 25]
    resident_4_off = [5, 6, 7, 8]
    resident_5_off = [3, 8, 12, 20]
#   workers_per_weekday = [2, 1, 2, 2, 2, 1, 2]

    # create Model
    model = cp_model.CpModel()
    # Sets limit for created solutions
    solution_limit = 10000

    # Creates shift variables.
    # shifts[(r, d)]: resident 'r' works on day 'd'.
    shifts = {}
    for r in all_residents:
        for d in all_days:
            shifts[(r, d)] = model.NewBoolVar('shift_r%id%i' % (r, d))
    
    # pprint(shifts)

    # Each shift is assigned to exactly one resident in the schedule period.
    for d in all_days:
            model.Add((sum(shifts[(r, d)] for r in all_residents) < 3 ))
    for d in all_days:
            model.Add((sum(shifts[(r, d)] for r in all_residents) > 0 ))
    

    # min_shifts_per_resident is the largest integer such that every resident
    # can be assigned at least that many shifts. If the number of residents doesn't
    # divide the total number of shifts over the schedule period,
    # some residents have to work one more shift, for a total of
    # resident + 1.
    min_shifts_per_resident = 8
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

    # Add constraint to prevent residents from working two consecutive days
    for r in all_residents:
        for d in all_days:
            if d < 29:
                next_day = d+1
                model.Add(
                    (shifts[(r, d)] + shifts[(r, next_day)]) <= 1
                )

    # Add constraint to ensure working friday + sunday if set to true


    if friday_sunday:
        for r in all_residents:
            for d in all_days:
                if calendar_weekdays[d] == 4 and d < 27:
    #               pprint("Busqueda de viernes...")
    #               pprint(f"Par de Viernes y domingo para residente {r}:")
    #               pprint(f"Viernes: {shifts[(r, d)]}")
    #               pprint(f"Domingo: {shifts[(r, d+2)]}")
                    model.AddBoolAnd([shifts[(r, d)], shifts[r, d+2]]).OnlyEnforceIf(shifts[(r, d)])
                    

    # Creates the solver and solve.
    solver = cp_model.CpSolver()
    solver.parameters.linearization_level = 0

    # Display the first five solutions.
    a_few_solutions = range(5)
    solution_printer = ResidentsPartialSolutionPrinter(shifts, num_residents,
                                                    num_days, a_few_solutions, weekday_names, calendar_weekdays, solution_limit)

    solver.SearchForAllSolutions(model, solution_printer)

    # Statistics.
    print()
    print('Statistics')
    print(f'  - conflicts       : {solver.NumConflicts()}')
    print(f'  - branches        : {solver.NumBranches()}')
    print(f'  - wall time       : {solver.WallTime()} s')
    print(f'  - solutions found : {solution_printer.solution_count() + 1}')

def _update_weekday(weekday):
    if weekday < 6:
        return weekday + 1
    elif weekday == 6:
        return 0

def _assign_weekdays(first_day, days):
    days_weeks = {}
    current_weekday = first_day
    for d in days:
        days_weeks[d] = current_weekday
        current_weekday = _update_weekday(current_weekday)
    return days_weeks

if __name__ == '__main__':
    main()