import shapefile
import matplotlib.pyplot as plt
import random
import matplotlib
import math
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QSizePolicy, QMessageBox, QWidget, QPushButton
from PyQt5.QtGui import QIcon


from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

matplotlib.use('Qt5Agg')
"""
What: Creates a dictionary lookup for zips to population of that zip
In: None
Out: Dictionary{Zip Code : Population}
"""
def zip_population_generator():
  zip_pop = {}
  with open("Maryland Population.csv", 'r') as pop:
    data = pop.readlines()
    data = data[1:]

    for line in data:
      line = line.strip().split(',')
      zip_pop[str(line[0])] = int(line[1])
      #print(line.strip())

  return zip_pop

"""
What: Finds center of a zip code based on points
In: {Zip Code : [Points]
Out: {Zip Code : (Center Point)
"""
def zip_codes_place_generator(zip_points):
  zip_places = {}

  for zip in zip_points.keys():
    x = 0
    y = 0
    for point in zip_points[zip]:
      x += point[0]
      y += point[1]
    zip_places[zip] = (x / len(zip_points[zip]), y / len(zip_points[zip]))

  return zip_places

"""
What: Returns all shapes that are associated with a specific zip code
In: [Zip Shapes]
Out: Dictionary{Zip Code: [list of all shapes in zip code]
"""
def zip_codes_generator(zip_shapes):
  zip_codes = {}
  for shape in zip_shapes:
    zip = shape.record[8]

    #If our shape is a body of water
    if zip == '':
      continue

    #If our shape is Assateague
    if zip == '00000':
      continue

    if(zip in zip_codes.keys()):
      zip_codes[zip].append(shape)
    else:
      zip_codes[zip] = [shape]

  return zip_codes

"""
What: Gets all points that are associated with a zip code
In: Dictionary{Zip Code : [list of all shapes in zip code]
Out: Dictionary{ Zip Code : set(Points of zip code)
"""
def zip_points_generator(zip_codes):
  zip_points = {}
  for zip_code in zip_codes.keys():
    zip_points[zip_code] = set()
    for part in zip_codes[zip_code]:
      zip_points[zip_code] = zip_points[zip_code] | set(part.shape.points)

  return zip_points

"""
What: Gets zip codes that are directly touching one another
In: Dictionary{Zip Code : set(Points of zip code)}
Out: Dictionary{Zip Code : [Zip Codes touching it]}
"""
def adjacent_zips(zip_points):
  adj = {}

  all_zips = zip_points.keys()

  #Find Neighbors
  for zip1 in zip_points.keys():
    for zip2 in zip_points.keys():
      if zip1 == zip2:
        continue
      if not zip_points[zip1].isdisjoint(zip_points[zip2]):
        if zip1 in adj:
         adj[zip1].append(zip2)
        else:
          adj[zip1] = [zip2]

  #Include zips that have no neighbors
  for zip_code in all_zips:
    if zip_code not in adj.keys():
      adj[zip_code] = []

  return adj

"""
What: Sees if all zip codes in a list are next to each other
In: [Zips to compare], {Zip Code : Adjacent Zip Codes}
Out: If all zip codes are adjacent
"""
def is_a_neighbor(zips, adjacent_zip_codes):

  for zip1 in zips:
    for zip2 in zips:
      if zip1 == zip2:
        continue
      elif zip2 in adjacent_zip_codes[zip1]:
        return False

  return True

"""
What: Return random seed zip codes
In: num_dists: Number of districts to create, {Zip Code : Adjacent Zip Codes}
Out: [distinct zip codes that are not next to each other with len(num_dists)]"""
def get_random_dist_seeds(adjacent_zip_codes, num_dists):
  districts = []
  first_run = True
  while(not is_a_neighbor(districts, adjacent_zip_codes) or first_run):
    districts = []
    first_run = False
    zips = list(adjacent_zip_codes.keys())
    for i in range(num_dists):
      seed = random.randint(0,len(zips) - 1)
      districts.append(zips[seed])
      zips.pop(seed)

  return districts
"""
What: Computes the distances between two zip codes
In: (Center point of zip code a), (Center point of zip code b)
Out: distance
"""
def compute_dist(point1, point2):
  return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

"""
What: Gets the closest zip code to a district that has the highest population (out of 5)
In: [Zips that make up a district], {Zip Code : [(Points belonging to zip code)], {Zip codes that have not been put into a district yet}, {Zip code : Population}
Out: Best choice to use for zip code"""
def get_closest(district, zip_points, free_zips, zip_population):

  current_points = set()
  closest_zips = set()
  for dist in district:
    try:
      current_points.add(zip_points[dist])
    except KeyError:
      print("Why2")
  top_3_dists = []
  highest_dist_index = 0
  for zip1 in district:
    for zip2 in free_zips:

      #Fill up the list
      if len(top_3_dists) != 2:
        top_3_dists.append(zip2)
        continue

      #Compute the most unreasonable zip code to have
      for zip3 in top_3_dists:
        if compute_dist(zip_points[zip1], zip_points[top_3_dists[highest_dist_index]]) < compute_dist(zip_points[zip1], zip_points[zip3]) :
          highest_dist_index = top_3_dists.index(zip3)

      #Replace it if we found a smaller one
      if compute_dist(zip_points[top_3_dists[highest_dist_index]], zip_points[zip1]) > compute_dist(zip_points[zip2], zip_points[zip1]):
        top_3_dists[highest_dist_index] = zip2
  print(len(free_zips))
  most_pop = top_3_dists[0]
  for zip in top_3_dists:
    try:
      if zip_population[zip] < zip_population[most_pop]:
        most_pop = zip
    except KeyError:
      print("Oh well")

  return most_pop

"""
In: {Zip codes that make up a district}, {Zip Code: Adjacent zip codes}
Out: (Zip code that will increase the population the most, and any zip codes with no population data so we can just suck them up)
"""
def find_best_neighbor(district, adjacent_zip_codes, free_zips, population_data, zip_positions):

  if(len(free_zips) == 0):
    print("Break here bitchhh")
  possible_solutions = set()

  for dist in district:
    try:
      for sol in adjacent_zip_codes[dist]:
        possible_solutions.add(sol)
    except KeyError:
      print(sol)
      print("why")

  #So we can index the first one just for sake of having a starting point
  possible_solutions = possible_solutions - set(district)
  possible_solutions = list(possible_solutions & free_zips)
  #print(possible_solutions)
  #print(district)
  best_solution = None
  try:
    best_solution = list(possible_solutions)[0]
  except IndexError:
    print("Oh well")

  #In case there is a zip codes with no population
  actual_solutions = []

  for solution in possible_solutions:
    try:
      if population_data[best_solution] < population_data[solution]:
        best_solution = solution
    except KeyError:
      actual_solutions.append(solution)

  if best_solution != None:
    actual_solutions.append(best_solution)

  #YIKE! Look for solutions that are CLOSE to us
  if actual_solutions == []:
    actual_solutions.append( get_closest(district, zip_positions, free_zips, population_data))
    #if('2' in actual_solutions):
     # print("wtf")

  return actual_solutions


"""
In: Number of districts to make, {Zip Code : [Adjacent Zip Codes]}, {Zip Code : Population}
Out: [set(continuable zips) * num_dists]
"""
def create_districts(num_dists, adjacent_zip_codes, population_data, zip_positions, total_population):
  #Get a list of all zip codes that are available
  free_zips = adjacent_zip_codes.keys()
  pop_per_dist = total_population / num_dists
  #Get random districts to start off with
  districts_seeds = get_random_dist_seeds(adjacent_zip_codes, num_dists)

  #Convert the seeds to a list of lists, and remove them from the "free" list
  districts = []
  for dist in districts_seeds:
    districts.append({dist})
    free_zips = free_zips - set(dist)

  #print("Break here")
  last_run = 0
  while(len(free_zips) != 0):
    #print(free_zips)
    #print(len(free_zips))
    for i in range(len(districts)):
      if(len(free_zips) == 0):
        print("WE GUCCI")
        return districts
      sol = find_best_neighbor(districts[i], adjacent_zip_codes, free_zips, population_data, zip_positions)
      if sol == []:
        last_run+=1
      else:
        last_run = 0

      if (last_run == num_dists):
        print(free_zips)
        return districts

      free_zips = free_zips - set(sol)
      districts[i] = list(set(districts[i]) | set(sol))

  #for dist in districts:
    ###print(dist)

  return districts

def main():

  colors = {"firebrick", "darksalmon", "tan", "gold", "lightseagreen", "darkturquoise", "deepskyblue", "navy", "royalblue", "coral", "peachpuff", "lawngreen", "cadetblue", "skyblue", "hotpink", "pink", "indigo", "yellow", "aqua", "pink", "crimson", "cadetblue", "maroon", "steelblue"}

  sf = shapefile.Reader("Maryland")
  srs = sf.shapeRecords()

  zip_population = zip_population_generator()

  zip_codes = zip_codes_generator(srs)
  zip_points = zip_points_generator(zip_codes)
  adjacent_zipcodes = adjacent_zips(zip_points)
  zip_population = zip_population_generator()
  zip_stuff = zip_codes_place_generator(zip_points)
  #for key in zip_codes.keys():
    #if(key not in zip_population.keys()):
      #print("zip code: ", key, " does not have population data")

  total_population = 0
  for key in zip_population.keys():
    total_population += zip_population[key]

 # print("Population: ", total_population)
  num_dists = 8
  dists = create_districts(num_dists, adjacent_zipcodes, zip_population, zip_stuff, total_population)

  cool = False
  while(not cool):
    cool = True
    for dist in dists:
      if not len(dist) > ((len(adjacent_zipcodes.keys()) - 20) / num_dists):
        cool = False
    if not cool:
      dists = create_districts(num_dists, adjacent_zipcodes, zip_population, zip_stuff, total_population)


  fig = plt.figure()
  ax = fig.add_subplot(111)
  plt.xlim([-80, -60])
  plt.ylim([20, 40])

  pointsaaa = {}

  """for shape in srs:
    points = shape.shape.points

    ap = plt.Polygon(points, fill=False, edgecolor="k")
    ap.set_fill(True)
    ap.set_color("red")
    ax.add_patch(ap)

  plt.show()
"""
  for zip in zip_points.keys():
    pointsaaa[zip] = []
    for point in zip_points[zip]:

      pointsaaa[zip].append((point[0], point[1]))

    print(pointsaaa[zip])

  for dist in dists:
    if(colors == None):
      print("WHY")
    c = list(colors)[0]
    colors.remove(c)
    for zip in dist:
      for shape in zip_codes[zip]:
        ap = plt.Polygon(shape.shape.points, fill=True, edgecolor="k")
        ap.set_color(c)

        ax.add_patch(ap)

  plt.show()
  plt.close()


if(__name__ == '__main__'):
  main()
