import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """

        #Iterate on each var and than on each words to remove the ones that are not the same length
        for var in self.domains:
            for word in self.domains[var].copy():
                if var.length != len(word):
                    self.domains[var].remove(word)


    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        flag = False

        wordsToRemove = []

        overlap = self.crossword.overlaps.get((x, y))

        if overlap:
            xIndex, yIndex = overlap

            # We have an overlap
            for xWord in self.domains[x].copy():
                removeWord = True
                
                for yWord in self.domains[y].copy():
                    # We need to verify if the two word can satisfy this overlap
                    if xWord[xIndex] == yWord[yIndex]:
                        # yWord satisfies the condition, no need to remove a word from x's domain
                        removeWord = False
                        break

                if removeWord:
                    # If no yWord is correct, we need to remove xWord from x's domain
                    wordsToRemove.append(xWord)
                    flag = True
        # Remove the needed words from x's domain 
        for word in wordsToRemove:
            self.domains[x].remove(word)
                        
        return flag

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        
        # In this case, the arcs are the overlaps

        if arcs is None:
            arcs = []
            # If no arcs list is specified, we build a queue containing all the arcs
            for overlap in self.crossword.overlaps:
                arcs.append(overlap)
    
        # Once we have our queue, we pop every item ensuring arc consistency for each
        while arcs:
            # pop the first element (FIFO)
            currentArc = arcs.pop(0)
            #print(currentArc)
            if self.revise(currentArc[0], currentArc[1]):
                if not self.domains[currentArc[0]]:
                    # If the modified domain is now empty, return False
                    return False
                # currentArc[0] variable was modified,we need to add the variables
                # that share a constraint with currentArc[0] in the queue
                for neighbor in self.crossword.neighbors(currentArc[0]):
                    if (neighbor, currentArc[0]) not in arcs:
                        arcs.append((neighbor, currentArc[0]))

        return True
        


    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        
        for var in self.domains:
            if var not in assignment or assignment[var] is None:
                return False
            
        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        
        # First we want to make sure there are no ducplicates in the dictionary values
        # To do so we will create a list and a set with all the values, if the len of the 
        # two is not the same, there are duplicates (Sets get rid of ducplicates)

        print(assignment)
        variables = list(assignment.values())
        print(variables)
        setVariables = set(variables)

        if len(variables) != len(setVariables):
            return False

        # Then we want to make sure the lengths are correct and that there are no conflicts
        # between neighboring variables
        for var in assignment:
            print(assignment[var])
            if (var.length != len(assignment[var])):
                return False
            neighbors = self.crossword.neighbors(var)
            
            if neighbors:
                for neighbor in neighbors:
                    overlap = self.crossword.overlaps.get((var, neighbor))
                    if overlap and neighbor in assignment:
                        # If there is an overlap and the neighbor is in assignment, we need to verify
                        # if the overlap is satisfied
                        xIndex, yIndex = overlap
                        if assignment[var][xIndex] != assignment[neighbor][yIndex]:
                            return False
                    #assignment[var][self.crossword.overlaps[var, neighbor][0]] != assignment[neighbor][self.crossword.overlaps[var, neighbor][1]]:
        
        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """

        words = []
        n = {}

        for word in self.domains[var]:
            words.append(word)
            n[word] = 0
            for neighbor in self.crossword.neighbors(var):
                # If the neighbor is not in assignment and and the word is in the neighbor's domain
                if neighbor not in assignment and word in self.domains[neighbor]:
                    # We add 1 to n
                    n[word] += 1

        print(n)
        # We return the sorted words list depending on the n values associated with each word
        res = sorted(words, key=lambda w: n[w])

        return res

                    
        #return list(word for word in self.domains[var] if word not in assignment)

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        
        minValues = float('inf')
        currentMinVar = None
        
        for var in self.domains:
            
            if var not in assignment:
                if len(self.domains[var]) < minValues:
                    minValues = len(self.domains[var])
                    currentMinVar = var

        return currentMinVar


    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        # If the assignment received is already complete and consistent we return it
        if self.assignment_complete(assignment) and self.consistent(assignment):
            return assignment

        var = self.select_unassigned_variable(assignment)
        

        for value in self.domains[var]:
            # Need to make sure that this value is not already assigned
            if value not in assignment.values():
                assignment[var] = value
                result = self.backtrack(assignment)
                if result:
                    return result
                assignment[var] = None
        
        return None



def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
