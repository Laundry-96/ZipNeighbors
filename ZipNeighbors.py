import shapefile

import matplotlib
import matplotlib.pyplot as plt
import random
import math
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QSizePolicy, QMessageBox, QWidget, QPushButton
from PyQt5.QtGui import QIcon


from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

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
def get_random_dist_seed(free_zips):

  zips = list(free_zips)
  seed = random.randint(0,len(zips) - 1)
  return zips[seed]

"""
What: Computes the distances between two zip codes
In: (Center point of zip code a), (Center point of zip code b)
Out: distance
"""
def compute_dist(point1, point2):
  return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)


def get_closest_district(zip, districts, zip_points):
  smallest_dist = None
  cur_points = zip_points[zip]
  for zip1 in zip_points.keys():
    is_in_a_dist = False
    for dist in districts:
      if not {zip1}.isdisjoint(set(dist)):
        is_in_a_dist = True
    if not is_in_a_dist:
      continue

    if zip1 == zip:
      continue

    if(smallest_dist == None):
      smallest_dist = zip1

    if compute_dist(zip_points[zip1], zip_points[zip]) < compute_dist(zip_points[smallest_dist], zip_points[zip]):
      smallest_dist = zip1

  for i in range(len(districts)):
    if not {smallest_dist}.isdisjoint(set(districts[i])):
      smallest_dist = i
      break

  return smallest_dist


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

  for zip in district:
    try:
      for sol in adjacent_zip_codes[zip]:
        possible_solutions.add(sol)
    except TypeError:
      print("WHYYY")
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
    #print("NO BEST SOLUTION")
    actual_solutions.append(best_solution)

  #YIKE! Look for solutions that are CLOSE to us
  #if actual_solutions == []:
    #actual_solutions.append( get_closest(district, zip_positions, free_zips, population_data))
    #if('2' in actual_solutions):
     # print("wtf")

  return actual_solutions




def create_districts(num_dists, adjacent_zip_codes, population_data, zip_positions, total_population):
  #Get a list of all zip codes that are available
  free_zips = set(adjacent_zip_codes.keys())
  pop_per_dist = total_population / num_dists
  #Get random districts to start off with
  districts = []
  for i in range(num_dists):
    dist_pop = 0
    print(len(free_zips))
    seed = get_random_dist_seed(free_zips)
    free_zips = free_zips - {seed}
    dist = []
    dist.append(seed)

    while(dist_pop < ((total_population / num_dists) - (total_population * num_dists * .001))):
      to_add = find_best_neighbor(dist, adjacent_zip_codes, free_zips, population_data, zip_positions)
      if to_add == []:
        break
      free_zips = free_zips - set(to_add)
      for zip in to_add:
        try:
          dist_pop += population_data[zip]
        except KeyError:
          dist_pop += 0
        dist.append(zip)

    districts.append(dist)
  
  print(len(free_zips))
  i = 0

  while not len(free_zips) == 0:
    for free_zip in free_zips:
      i+=1
      print("running: ", i)
      adj = set(adjacent_zip_codes[free_zip])
      found = False
      for district in districts:
        if(not set(district).isdisjoint(adj)):
          found = True
          district.append(free_zip)
          free_zips = free_zips - {free_zip}
          break
      if(not found):

        districts[get_closest_district(free_zip, districts, zip_positions)].append(free_zip)
      free_zips = free_zips - {free_zip}

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
  
  total_population = 0
  for key in zip_population.keys():
    total_population += zip_population[key]

  pointsaaa = {}

  for zip in zip_points.keys():
    pointsaaa[zip] = []
    for point in zip_points[zip]:

      pointsaaa[zip].append((point[0], point[1]))

  num_dists = 12
  dists = create_districts(num_dists, adjacent_zipcodes, zip_population, zip_stuff, total_population)
  
  fig = plt.figure()
  ax = fig.add_subplot(111)
  plt.xlim([-80, -60])
  plt.ylim([20, 40])

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
