import linkage

genome = linkage.genome.GearPivotGenome.random_genome(200)
specie = linkage.genome.GearPivotSpecie()
specie.parse(genome)

gv = linkage.visualization.GraphViz()
gv.render(specie.graph, "pre_normalize")
specie.normalize_graph()
gv.render(specie.graph, "post_normalize")
