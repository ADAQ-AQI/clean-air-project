import sys

# f= open(sys.argv[1], mode= 'rt', encoding='utf-8')
f = open('testdata.txt', mode='rt', encoding='utf-8')

#Call open file using a with block to ensure it gets closed at end
print('\nOpening (using with)',f.name)
with open('testdata.txt', mode='rt', encoding='utf-8')as file:
    for line in file:
        #Do some processing on the file
        sys.stdout.write(line)

        #Filter out the word data

        #write to dataobject

