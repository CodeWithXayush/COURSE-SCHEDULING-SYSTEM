import random
from collections import defaultdict
from typing import List, Dict, Tuple, Set

class Course:
    def __init__(self, name: str, capacity: int, professor: str, department: str, student_group: str):
        self.name = name
        self.capacity = capacity
        self.professor = professor
        self.department = department
        self.student_group = student_group

class Room:
    def __init__(self, name: str, capacity: int):
        self.name = name
        self.capacity = capacity

class TimeSlot:
    def __init__(self, day: str, start_time: str, end_time: str):
        self.day = day
        self.start_time = start_time
        self.end_time = end_time

    def __str__(self):
        return f"{self.day} {self.start_time}-{self.end_time}"

class Schedule:
    def __init__(self):
        self.assignments: Dict[Tuple[Course, Room, TimeSlot], str] = {}

    def assign(self, course: Course, room: Room, time_slot: TimeSlot):
        self.assignments[(course, room, time_slot)] = course.student_group

    def remove(self, course: Course, room: Room, time_slot: TimeSlot):
        self.assignments.pop((course, room, time_slot), None)

    def get_conflicts(self) -> int:
        conflicts = 0
        professor_schedule = defaultdict(list)
        student_group_schedule = defaultdict(list)

        for (course, room, time_slot), student_group in self.assignments.items():
            # Check room capacity
            if course.capacity > room.capacity:
                conflicts += 1

            # Check professor conflicts
            if time_slot in professor_schedule[course.professor]:
                conflicts += 1
            professor_schedule[course.professor].append(time_slot)

            # Check student group conflicts
            if time_slot in student_group_schedule[student_group]:
                conflicts += 1
            student_group_schedule[student_group].append(time_slot)

        return conflicts

    def __str__(self):
        result = []
        for (course, room, time_slot), student_group in self.assignments.items():
            result.append(f"{room.name} at {time_slot}: {course.name} (Prof. {course.professor}) - {student_group}")
        return "\n".join(result)

def generate_random_schedule(courses: List[Course], rooms: List[Room], time_slots: List[TimeSlot]) -> Schedule:
    schedule = Schedule()
    for course in courses:
        room = random.choice(rooms)
        time_slot = random.choice(time_slots)
        schedule.assign(course, room, time_slot)
    return schedule

def get_neighbors(schedule: Schedule, courses: List[Course], rooms: List[Room], time_slots: List[TimeSlot]) -> List[Schedule]:
    neighbors = []
    for course, room, time_slot in schedule.assignments:
        for new_room in rooms:
            if new_room != room:
                new_schedule = Schedule()
                new_schedule.assignments = schedule.assignments.copy()
                new_schedule.remove(course, room, time_slot)
                new_schedule.assign(course, new_room, time_slot)
                neighbors.append(new_schedule)
        
        for new_time_slot in time_slots:
            if new_time_slot != time_slot:
                new_schedule = Schedule()
                new_schedule.assignments = schedule.assignments.copy()
                new_schedule.remove(course, room, time_slot)
                new_schedule.assign(course, room, new_time_slot)
                neighbors.append(new_schedule)
    
    return neighbors

def hill_climbing(courses: List[Course], rooms: List[Room], time_slots: List[TimeSlot], max_iterations: int = 1000) -> Schedule:
    current_schedule = generate_random_schedule(courses, rooms, time_slots)
    current_conflicts = current_schedule.get_conflicts()

    for _ in range(max_iterations):
        neighbors = get_neighbors(current_schedule, courses, rooms, time_slots)
        best_neighbor = min(neighbors, key=lambda s: s.get_conflicts())
        best_neighbor_conflicts = best_neighbor.get_conflicts()

        if best_neighbor_conflicts >= current_conflicts:
            break

        current_schedule = best_neighbor
        current_conflicts = best_neighbor_conflicts

        if current_conflicts == 0:
            break

    return current_schedule

def ac3(courses: List[Course], rooms: List[Room], time_slots: List[TimeSlot]) -> Dict[Course, List[Tuple[Room, TimeSlot]]]:
    def remove_inconsistent_values(course1: Course, course2: Course, domains: Dict[Course, List[Tuple[Room, TimeSlot]]]) -> bool:
        removed = False
        for room1, time_slot1 in domains[course1][:]:
            if all(
                (room1 == room2 and time_slot1 == time_slot2) or
                (course1.professor == course2.professor and time_slot1 == time_slot2) or
                (course1.student_group == course2.student_group and time_slot1 == time_slot2)
                for room2, time_slot2 in domains[course2]
            ):
                domains[course1].remove((room1, time_slot1))
                removed = True
        return removed

    domains = {course: [(room, time_slot) for room in rooms for time_slot in time_slots] for course in courses}
    queue = [(course1, course2) for course1 in courses for course2 in courses if course1 != course2]

    while queue:
        course1, course2 = queue.pop(0)
        if remove_inconsistent_values(course1, course2, domains):
            for course in courses:
                if course != course1 and course != course2:
                    queue.append((course, course1))

    return domains

def dfs_with_ac3(courses: List[Course], rooms: List[Room], time_slots: List[TimeSlot]) -> Schedule:
    def is_valid_assignment(schedule: Schedule, course: Course, room: Room, time_slot: TimeSlot) -> bool:
        if course.capacity > room.capacity:
            return False

        for (c, r, t), sg in schedule.assignments.items():
            if t == time_slot:
                if c.professor == course.professor:
                    return False
                if sg == course.student_group:
                    return False

        return True

    def backtrack(schedule: Schedule, unassigned_courses: List[Course], domains: Dict[Course, List[Tuple[Room, TimeSlot]]]) -> bool:
        if not unassigned_courses:
            return True

        course = min(unassigned_courses, key=lambda c: len(domains[c]))
        for room, time_slot in domains[course]:
            if is_valid_assignment(schedule, course, room, time_slot):
                schedule.assign(course, room, time_slot)
                new_domains = {c: d[:] for c, d in domains.items()}
                new_domains[course] = [(room, time_slot)]
                
                # Propagate constraints
                for other_course in unassigned_courses:
                    if other_course != course:
                        new_domains[other_course] = [
                            (r, t) for r, t in new_domains[other_course]
                            if not (
                                (r == room and t == time_slot) or
                                (other_course.professor == course.professor and t == time_slot) or
                                (other_course.student_group == course.student_group and t == time_slot)
                            )
                        ]
                        if not new_domains[other_course]:
                            schedule.remove(course, room, time_slot)
                            break
                else:
                    if backtrack(schedule, [c for c in unassigned_courses if c != course], new_domains):
                        return True
                
                schedule.remove(course, room, time_slot)

        return False

    initial_domains = ac3(courses, rooms, time_slots)
    schedule = Schedule()
    if backtrack(schedule, courses, initial_domains):
        return schedule
    else:
        return None  # No valid schedule found

# ... [All previous class definitions and functions remain the same]

def compare_schedules(hc_schedule: Schedule, ac3_dfs_schedule: Schedule) -> Schedule:
    hc_conflicts = hc_schedule.get_conflicts()
    ac3_dfs_conflicts = ac3_dfs_schedule.get_conflicts() if ac3_dfs_schedule else float('inf')
    
    if hc_conflicts == 0 and ac3_dfs_conflicts == 0:
        # Both schedules have 0 conflicts, compare based on additional criteria
        return compare_zero_conflict_schedules(hc_schedule, ac3_dfs_schedule)
    elif ac3_dfs_conflicts == 0:
        return ac3_dfs_schedule
    elif hc_conflicts < ac3_dfs_conflicts:
        return hc_schedule
    else:
        return ac3_dfs_schedule

def compare_zero_conflict_schedules(schedule1: Schedule, schedule2: Schedule) -> Schedule:
    # Compare schedules based on the number of days used
    days_used1 = len(set(time_slot.day for (_, _, time_slot) in schedule1.assignments))
    days_used2 = len(set(time_slot.day for (_, _, time_slot) in schedule2.assignments))
    
    if days_used1 < days_used2:
        return schedule1
    elif days_used2 < days_used1:
        return schedule2
    else:
        rooms_used1 = len(set(room for (_, room, _) in schedule1.assignments))
        rooms_used2 = len(set(room for (_, room, _) in schedule2.assignments))
        if rooms_used1<rooms_used2:
            return schedule1
        else:
            return schedule2

def print_schedule(schedule: Schedule, algorithm_name: str):
    print(f"\n{algorithm_name} Schedule:")
    print(schedule)
    print(f"Conflicts: {schedule.get_conflicts()}")

def main():
    courses = [
        Course("Math 101", 30, "Dr. Smith", "Mathematics", "CSE-A"),
        Course("Math 102", 35, "Dr. Smith", "Mathematics", "CSE-B"),
        Course("Physics 201", 25, "Dr. Johnson", "Physics", "CSE-A"),
        Course("Physics 202", 30, "Dr. Johnson", "Physics", "CSE-B"),
        Course("Chemistry 301", 20, "Dr. Brown", "Chemistry", "CSE-A"),
        Course("Chemistry 302", 25, "Dr. Brown", "Chemistry", "CSE-B"),
        Course("Computer Science 401", 40, "Dr. Davis", "Computer Science", "CSE-A"),
        Course("Computer Science 402", 35, "Dr. Davis", "Computer Science", "CSE-B"),
    ]

    rooms = [
        Room("Room A", 40),
        Room("Room B", 35),
        Room("Room C", 30),
        Room("Room D", 25),
    ]

    time_slots = [
        TimeSlot("Monday", "09:00", "10:30"),
        TimeSlot("Monday", "11:00", "12:30"),
        TimeSlot("Monday", "14:00", "15:30"),
        TimeSlot("Tuesday", "09:00", "10:30"),
        TimeSlot("Tuesday", "11:00", "12:30"),
        TimeSlot("Tuesday", "14:00", "15:30"),
        TimeSlot("Wednesday", "09:00", "10:30"),
        TimeSlot("Wednesday", "11:00", "12:30"),
        TimeSlot("Wednesday", "14:00", "15:30"),
    ]

    hc_schedule = hill_climbing(courses, rooms, time_slots)
    print_schedule(hc_schedule, "Hill Climbing")

    ac3_dfs_schedule = dfs_with_ac3(courses, rooms, time_slots)
    if ac3_dfs_schedule:
        print_schedule(ac3_dfs_schedule, "AC-3 + DFS")
    else:
        print("\nAC-3 + DFS Algorithm: No valid schedule found")

    optimal_schedule = compare_schedules(hc_schedule, ac3_dfs_schedule)

    print("\nConclusion:")
    if optimal_schedule == ac3_dfs_schedule and ac3_dfs_schedule is not None:
        print("The AC-3 + DFS algorithm produced the optimal schedule with no conflicts.")
    elif optimal_schedule == hc_schedule:
        print("The Hill Climbing algorithm produced the schedule with fewer conflicts.")
        if ac3_dfs_schedule is None:
            print("The AC-3 + DFS algorithm couldn't find a valid schedule.")
    else:
        print("Both algorithms produced schedules with conflicts, but AC-3 + DFS had fewer.")

    print("\nOptimal Schedule:")
    print(optimal_schedule)
    print(f"Conflicts: {optimal_schedule.get_conflicts()}")

if __name__ == "__main__":
    main()