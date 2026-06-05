import time

def timer(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start} seconds")
        return result
    return wrapper

@timer      #get_patients = timer(get_patients)
def get_patients():
    return [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
# Now check from OUTSIDE:
print(get_patients.__name__)  # wrapper      ← identity lost
print(get_patients.__doc__)   # None         ← docstring lost
get_patients()


import functools

# WITHOUT functools.wraps
def decorator_bad(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

# WITH functools.wraps
def decorator_good(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@decorator_bad
def say_hello():
    """Says hello."""
    pass

@decorator_good
def say_goodbye():
    """Says goodbye."""
    pass

print("Without functools.wraps:")
print(f"  name: {say_hello.__name__}")   # wrapper
print(f"  doc:  {say_hello.__doc__}")    # None

print("With functools.wraps:")
print(f"  name: {say_goodbye.__name__}") # say_goodbye
print(f"  doc:  {say_goodbye.__doc__}")  # Says goodbye.