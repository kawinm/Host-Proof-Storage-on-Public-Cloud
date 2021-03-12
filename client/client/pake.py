from random import randint

prime_list = [48112959837082048697,
54673257461630679457,
29497513910652490397,
40206835204840513073,
12764787846358441471,
71755440315342536873,
45095080578985454453,
27542476619900900873,
66405897020462343733,
36413321723440003717]

p0 = randint(0,10)
p = prime_list[p0]
g1 = randint(10000000000000000000, p)
g2 = randint(10000000000000000000, p)

u = "kawin"
P = "secret#password"

a = []
for i in P:
    a.append(str(ord(i)))

a = "".join(a)
a = int(a)

aa = g2 ** a

dk1 = randint(10000000000000000000, p)
ek1 = g1 ** dk1

dk2 = randint(10000000000000000000, p)
ek2 = g1 ** dk2

print("p : ", p)
print("g1 : ", g1)
print("g2 : ". g2)
print("Pass : ", P)
print("P : ", a)
print("g2 ** p: ", aa)
print("dk1 x1: ", dk1)
print("ek1 : ", ek1)
print("dk2 x2: ", dk2)
print("ek2 : ", ek2)


