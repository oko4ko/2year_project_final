def glue(tokens):
    fin = ' '.join(tokens)
    fin = fin[0].upper() + fin[1:]
    for i in '.,:;()?!':
        fin = fin.replace(' ' + i, i)
    return fin
