# angle.py

def less(a, b):
    r'''Return true if a < b.

        >>> less(10, 20)
        True
        >>> less(20, 10)
        False
        >>> less(10, 10)
        False
        >>> less(-10, 10)
        True
        >>> less(10, -10)
        False
        >>> less(-20, -10)
        True
        >>> less(-10, -20)
        False
        >>> less(-10, -10)
        False
        >>> less(-170, 170)
        False
        >>> less(170, -170)
        True
    '''
    return 0 < (b - a) % 360 < 180

if __name__ == "__main__":
    import doctest
    doctest.testmod()
