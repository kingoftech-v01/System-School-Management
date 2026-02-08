from dz import dz_array

'''
A context processor is a function that accepts an argument and returns a dictionary as its output.
In our case, the returning dictionary is added as the context and the biggest advantage is that,
it can be accessed globally i.e, across all templates.
'''

def dz_static(request):
    return {"dz_array":dz_array}
