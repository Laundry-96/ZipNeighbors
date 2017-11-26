import shapefile

def adjacentZips(zips):
	adj = {}
	for zip1 in zips.keys():
		for zip2 in zips.keys():
			print("zip1: ", zip1, " zip2: ", zip2)
			if zip1 == zip2:
				continue
			if not zips[zip1].isdisjoint(zips[zip2]):
				if zip1 in adj:
					adj[zip1] = adj[zip1] | {zip2}
				else:
					adj[zip1] = {zip2}
	return adj

def main():
	zips = {}
	sf = shapefile.Reader("Maryland")
	srs = sf.shapeRecords()

	for sr in srs:
		if sr.record[8] == '':
			print("don't worry about it")
		elif sr.record[8] in zips:
			zips[sr.record[8]] = zips[sr.record[8]] | set(sr.shape.points)
		else:
			zips[sr.record[8]] = set(sr.shape.points)
	
	n = adjacentZips(zips)

	for zip in n.keys():
		print("Zip code: ", zip, " Neighbors: ", n[zip])

if(__name__ == '__main__'):
	main()
