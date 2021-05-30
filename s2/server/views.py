from django.shortcuts import render

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse

import random
import math
import sys
import json
import hashlib
from math import degrees, acos

from .models import Server

import hashlib
from base64 import b64encode, b64decode

from uuid import uuid4

def transposeMatrix(m):
    return list(map(list,zip(*m)))

def getMatrixMinor(m,i,j):
    return [row[:j] + row[j+1:] for row in (m[:i]+m[i+1:])]

def getMatrixDeternminant(m):
    #base case for 2x2 matrix
    if len(m) == 2:
        return m[0][0]*m[1][1]-m[0][1]*m[1][0]

    determinant = 0
    for c in range(len(m)):
        determinant += ((-1)**c)*m[0][c]*getMatrixDeternminant(getMatrixMinor(m,0,c))
    return determinant

def getMatrixInverse(m):
    determinant = getMatrixDeternminant(m)
    #special case for 2x2 matrix:
    if len(m) == 2:
        return [[m[1][1]/determinant, -1*m[0][1]/determinant],
                [-1*m[1][0]/determinant, m[0][0]/determinant]]

    #find matrix of cofactors
    cofactors = []
    for r in range(len(m)):
        cofactorRow = []
        for c in range(len(m)):
            minor = getMatrixMinor(m,r,c)
            cofactorRow.append(((-1)**(r+c)) * getMatrixDeternminant(minor))
        cofactors.append(cofactorRow)
    cofactors = transposeMatrix(cofactors)
    for r in range(len(cofactors)):
        for c in range(len(cofactors)):
            cofactors[r][c] = cofactors[r][c]/determinant
    return cofactors

def matrix_multiplication(X,Y):
    result = [[0 for j in range(len(Y[0]))] for i in range(len(X))]
    for i in range(len(X)):
        for j in range(len(Y[0])):
            for k in range(len(Y)):
                result[i][j] += X[i][k] * Y[k][j]
    return result

# computes the greatest common denominator of a and b.  assumes a > b
def gcd( a, b ):
    while b != 0:
        c = a % b
        a = b
        b = c
    return a

#computes base^exp mod modulus
def modexp( base, exp, modulus ):
    return pow(base, exp, modulus)

#solovay-strassen primality test.  tests if num is prime
def SS( num, iConfidence ):
    #ensure confidence of t
    for i in range(iConfidence):
        #choose random a between 1 and n-2
        a = random.randint( 1, num-1 )

        #if a is not relatively prime to n, n is composite
    if gcd( a, num ) > 1:
        return False

    #declares n prime if jacobi(a, n) is congruent to a^((n-1)/2) mod n
    if not jacobi( a, num ) % num == modexp ( a, (num-1)//2, num ):
        return False

        #if there have been t iterations without failure, num is believed to be prime
    return True

#computes the jacobi symbol of a, n
def jacobi( a, n ):
    if a == 0:
        if n == 1:
            return 1
        else:
            return 0
    #property 1 of the jacobi symbol
    elif a == -1:
        if n % 2 == 0:
            return 1
        else:
            return -1
    #if a == 1, jacobi symbol is equal to 1
    elif a == 1:
        return 1
    #property 4 of the jacobi symbol
    elif a == 2:
        if n % 8 == 1 or n % 8 == 7:
            return 1
        elif n % 8 == 3 or n % 8 == 5:
            return -1
    #property of the jacobi symbol:
    #if a = b mod n, jacobi(a, n) = jacobi( b, n )
    elif a >= n:
        return jacobi( a%n, n)
    elif a%2 == 0:
        return jacobi(2, n)*jacobi(a//2, n)
    #law of quadratic reciprocity
    #if a is odd and a is coprime to n
    else:
        if a % 4 == 3 and n%4 == 3:
            return -1 * jacobi( n, a)
        else:
            return jacobi(n, a )


#finds a primitive root for prime p
#this function was implemented from the algorithm described here:
#http://modular.math.washington.edu/edu/2007/spring/ent/ent-html/node31.html
def find_primitive_root( p ):
    if p == 2:
        return 1
    #the prime divisors of p-1 are 2 and (p-1)/2 because
    #p = 2x + 1 where x is a prime
    p1 = 2
    p2 = (p-1) // p1

    #test random g's until one is found that is a primitive root mod p
    while( 1 ):
        g = random.randint( 2, p-1 )
            #g is a primitive root if for all prime factors of p-1, p[i]
        #g^((p-1)/p[i]) (mod p) is not congruent to 1
        if not (modexp( g, (p-1)//p1, p ) == 1):
            if not modexp( g, (p-1)//p2, p ) == 1:
                return g

#encodes bytes to integers mod p.  reads bytes from file
def encode(sPlaintext, iNumBits):
    byte_array = bytearray(sPlaintext, 'utf-16')

    #z is the array of integers mod p
    z = []

    #each encoded integer will be a linear combination of k message bytes
    #k must be the number of bits in the prime divided by 8 because each
    #message byte is 8 bits long
    k = iNumBits//8

    #j marks the jth encoded integer
    #j will start at 0 but make it -k because j will be incremented during first iteration
    j = -1 * k
    #num is the summation of the message bytes
    num = 0
    #i iterates through byte array
    for i in range( len(byte_array) ):
        #if i is divisible by k, start a new encoded integer
        if i % k == 0:
            j += k
            num = 0
            z.append(0)
    #add the byte multiplied by 2 raised to a multiple of 8
        z[j//k] += byte_array[i]*(2**(8*(i%k)))

    #example
    #if n = 24, k = n / 8 = 3
    #z[0] = (summation from i = 0 to i = k)m[i]*(2^(8*i))
    #where m[i] is the ith message byte

    #return array of encoded integers
    return z

#decodes integers to the original message bytes
def decode(aiPlaintext, iNumBits):
    #bytes array will hold the decoded original message bytes
    bytes_array = []

        #same deal as in the encode function.
        #each encoded integer is a linear combination of k message bytes
        #k must be the number of bits in the prime divided by 8 because each
        #message byte is 8 bits long
    k = iNumBits//8

        #num is an integer in list aiPlaintext
    for num in aiPlaintext:
                #get the k message bytes from the integer, i counts from 0 to k-1
        for i in range(k):
                        #temporary integer
            temp = num
                        #j goes from i+1 to k-1
            for j in range(i+1, k):
                                #get remainder from dividing integer by 2^(8*j)
                temp = temp % (2**(8*j))
                        #message byte representing a letter is equal to temp divided by 2^(8*i)
            letter = temp // (2**(8*i))
                        #add the message byte letter to the byte array
            bytes_array.append(letter)
                        #subtract the letter multiplied by the power of two from num so
                        #so the next message byte can be found
            num = num - (letter*(2**(8*i)))

        #example
        #if "You" were encoded.
        #Letter        #ASCII
        #Y              89
        #o              111
        #u              117
        #if the encoded integer is 7696217 and k = 3
        #m[0] = 7696217 % 256 % 65536 / (2^(8*0)) = 89 = 'Y'
        #7696217 - (89 * (2^(8*0))) = 7696128
        #m[1] = 7696128 % 65536 / (2^(8*1)) = 111 = 'o'
        #7696128 - (111 * (2^(8*1))) = 7667712
        #m[2] = 7667712 / (2^(8*2)) = 117 = 'u'

    decodedText = bytearray(b for b in bytes_array).decode('utf-16')

    return decodedText

def PasswordToHex(P):
    a = []
    for i in P:
        a.append(str(ord(i)))
    pass_hex = int("".join(a))
    return pass_hex

def add_user(user):
    try:
        print("DB")

        id = "hpsdb"
        try:
            db = client.get_database_client(id)
            print('Database with id \'{0}\' was found, it\'s link is {1}'.format(id, db.database_link))

        except exceptions.CosmosResourceNotFoundError:
            print('A database with id \'{0}\' does not exist'.format(id))

        print("\n4. Get a Container by id")

        id = "users"
        try:
            container = db.get_container_client(id)
            print('Container with id \'{0}\' was found, it\'s link is {1}'.format(container.id, container.container_link))

        except exceptions.CosmosResourceNotFoundError:
            print('A container with id \'{0}\' does not exist'.format(id))

        print('Creating Items')

                # Create a SalesOrder object. This object has nested properties and various types including numbers, DateTimes and strings.
                # This can be saved as JSON as is without converting into rows/columns.
        container.create_item(body=user)

        #print('\n1.3 - Reading all items in a container\n')

                # NOTE: Use MaxItemCount on Options to control how many items come back per trip to the server
                #       Important to handle throttles whenever you are doing operations such as this that might
                #       result in a 429 (throttled request)
        #item_list = list(container.read_all_items(max_item_count=10))

        #print('Found {0} items'.format(item_list.__len__()))

        #for doc in item_list:
        #    print('Item Id: {0}'.format(doc.get('id')))
        return "success"
    except:
        return "failed"

def get_user(username):
    try:
        print("DB")

        id = "hpsdb"
        try:
            db = client.get_database_client(id)
            print('Database with id \'{0}\' was found, it\'s link is {1}'.format(id, db.database_link))

        except exceptions.CosmosResourceNotFoundError:
            print('A database with id \'{0}\' does not exist'.format(id))

        print("\n4. Get a Container by id")

        id = "users"
        try:
            container = db.get_container_client(id)
            print('Container with id \'{0}\' was found, it\'s link is {1}'.format(container.id, container.container_link))

        except exceptions.CosmosResourceNotFoundError:
            print('A container with id \'{0}\' does not exist'.format(id))

                # Create a SalesOrder object. This object has nested properties and various types including numbers, DateTimes and strings.
                # This can be saved as JSON as is without converting into rows/columns.
        query = "SELECT * FROM c WHERE c.username = '"+ username +"'"

        items = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        return items

        #print('\n1.3 - Reading all items in a container\n')

                # NOTE: Use MaxItemCount on Options to control how many items come back per trip to the server
                #       Important to handle throttles whenever you are doing operations such as this that might
                #       result in a 429 (throttled request)
        #item_list = list(container.read_all_items(max_item_count=10))

        #print('Found {0} items'.format(item_list.__len__()))

        #for doc in item_list:
        #    print('Item Id: {0}'.format(doc.get('id')))
        return "success"
    except:
        return "failed"

# Create your views here.
def index(request):
    try:
        req = json.loads(request.body)

        step = req['func']
        username = req['username']
        g2powP = int(req['g2powP'])

        if step == "register":
            bankname = req['bankname']
            location = req['location']

            p = int(req['p'])

            g1 = int(req['g1'])
            g2 = int(req['g2'])
            g3 = int(req['g3'])
            g4 = int(req['g4'])

            X2 = int(req['x2'])

            a1 = int(req['a1'])
            a2 = int(req['a2'])

            b2 = int(req['b2'])
            y1 = int(req['y1'])
            y2 = int(req['y2'])

            print(g4)
            print(g2powP)
            print(p)

            g4powg2powP = modexp(g4, g2powP, p)
            g4pow2powP_str = str(g4powg2powP)
            length = len(g4pow2powP_str)
            length_for_x = length // 9
            rem = length - length_for_x
            vertex = []
            for i in range(9):
                x = int(g4pow2powP_str[i*length_for_x: i*length_for_x + length_for_x])
                vertex.append(x)
            u4 = int(g4pow2powP_str[length_for_x*9: ])
            x4 = (vertex[0] + vertex[3] + vertex[6]) / 3 + u4
            y4 = (vertex[1] + vertex[4] + vertex[7]) / 3 + u4
            z4 = (vertex[2] + vertex[5] + vertex[8]) / 3 + u4
            vertex.append(x4)
            vertex.append(y4)
            vertex.append(z4)

            centroid = [0,0,0]
            for i in range(3):
                centroid[i] = ( vertex[i] + vertex[i+3] + vertex[i+6] + vertex[i+9] ) /4

            line1 = ((vertex[-1] **2) + (vertex[-2] **2) + (vertex[-3] ** 2)) ** (1/2)
            line2_points = [0,0,0]
            for i in range(3):
                line2_points[i] = (vertex[i+3] + vertex[i+6] + vertex[i+9] ) /3
            line2 = ((line2_points[-1] **2) + (line2_points[-2] **2) + (line2_points[-3] ** 2)) ** (1/2)

            print(line1/line2)
            if line1/line2 >= 1:
                theta = degrees(acos(line1/line2 - (line1//line2)))
            else:
                theta = degrees(acos(line1/line2))
            print(theta)


            A1 = modexp(int(g1), int(a1), int(p))
            B1 = (modexp(int(g2), int(theta), int(p)) * modexp(int(y1), int(a1), int(p))) % int(p)

            print("A1 : ", A1)
            print("B1 : ", B1)
            
            bankid = uuid4().hex
            
            #add_user(user)
            server = Server(user_name=username, p=p, g1=g1, g2=g2, g3=g3, g4=g4, A1=A1, B1=B1, x2=X2, a2=a2, b2=y2, bankname = bankname, location = location, bankid = bankid)
            server.save()

            response = {
                    'name': "s2",
                    'msg' : "success",
                    "id"  : str(bankid)
            }
            return JsonResponse(response)
    except Exception as e:
        print(e)
        response = {
                    'name': "s2",
                    'msg' : "failed"
            }
        return JsonResponse(response)


def login(request):
    try:
        req = json.loads(request.body)

        step = req['func']
        username = req['username']
        R1 = int(req['R1'])
        R2 = int(req['R2'])

        A1_dash = int(req['A1_d'])
        B1_dash = int(req['B1_d'])

        server = Server.objects.get(user_name=username)

        p = int(server.p)

        g1 = int(server.g1)
        g2 = int(server.g2)
        g3 = int(server.g3)
        g4 = int(server.g4)

        A1 = int(server.A1)
        B1 = int(server.B1)

        a2 = int(server.a2)
        y2 = int(server.b2)

        r1 = int(find_primitive_root(p))
        
        g4powg2powP = modexp(g4, R2, p)
        g4pow2powP_str = str(g4powg2powP)
        length = len(g4pow2powP_str)
        length_for_x = length // 9
        rem = length - length_for_x
        vertex = []
        for i in range(9):
            x = int(g4pow2powP_str[i*length_for_x: i*length_for_x + length_for_x])
            vertex.append(x)
        u4 = int(g4pow2powP_str[length_for_x*9: ])
        x4 = (vertex[0] + vertex[3] + vertex[6]) / 3 + u4
        y4 = (vertex[1] + vertex[4] + vertex[7]) / 3 + u4
        z4 = (vertex[2] + vertex[5] + vertex[8]) / 3 + u4
        vertex.append(x4)
        vertex.append(y4)
        vertex.append(z4)
        A = [[0,0,0],[0,0,0],[0,0,0]]
        A[0][0] = vertex[3] - vertex[0]
        A[1][0] = vertex[4] - vertex[1]
        A[2][0] = vertex[5] - vertex[2]

        A[0][1] = vertex[6] - vertex[3]
        A[1][1] = vertex[7] - vertex[4]
        A[2][1] = vertex[8] - vertex[5]

        A[0][2] = x4 - vertex[6]
        A[1][2] = y4 - vertex[7]
        A[2][2] = z4 - vertex[8]

        B = [[0],[0],[0]]
        B[0][0] = ((vertex[3]+vertex[4]+vertex[5]) - (vertex[0]+vertex[1]+vertex[2])) * 0.5
        B[1][0] = ((vertex[6]+vertex[7]+vertex[8]) - (vertex[3]+vertex[4]+vertex[5])) * 0.5
        B[2][0] = ((x4+y4+z4) - (vertex[6]+vertex[7]+vertex[8])) * 0.5

        A_inv = getMatrixInverse(A)

        omega = matrix_multiplication(A_inv, B)
        print(A)
        print(A_inv)
        print(B)
        print(omega)
        o = 0
        for i in omega:
            if i[0] < 0:
                i[0] *= -1
            o += i[0]
        omega = int(o)


        A2_dash = modexp(int(g1), int(a2), int(p))
        B2_dash = (modexp(int(g2), int(omega), int(p)) * modexp(int(y2), int(a2), int(p))) % int(p)
        

        if not (A1 == A1_dash and B1 == B1_dash):
            response = {
                'name': "s2",
                'msg' : "failed"
            }
            return JsonResponse(response)


        response = {
                'name': "s2",
                'msg' : "success",
                'A2_d': A2_dash,
                'B2_d': B2_dash
        }
        return JsonResponse(response)
    except Exception as e:
        print(e)
        response = {
                    'name': "s2",
                    'msg' : "failed"
            }
        return JsonResponse(response)