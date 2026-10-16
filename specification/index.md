# Simple Object Machine

## Language Specification

### Introduction

[SOM][SOM-st] is a minimal Smalltalk dialect which was used to teach VM
construction at the [Hasso Plattner Institute][SOM]. It was originally built at
the University of Århus (Denmark) for teaching.

Currently, SOM is maintained as a research and teaching tool and has its home
at: [https://som-st.github.io][SOM-st]


### Core Library

#### Integer Class

Integers in SOM have arbitrary precision, which means they are not strictly
word-sized or indeed have any other upper limited than the available memory.

All integers are an instance of class `Integer`.

In the following, we define all operations on `Integer`.

##### Addition

The addition of arbitrary-precision integers returns an arbitrary-precision
integer.

For example:

```{spec IntSpec.intAddition}
 3 + 4 = 7.
-4 + 3 = -1.
```

The addition of a `Double` value to an integer results in a `Double` value.

For example:

```{spec IntSpec.doubleAddition}
self expect:  3 + 4.4 toEqual:  7.4 within: 0.00000001.
self expect: -4 + 3.3 toEqual: -0.7 within: 0.00000001.
```

Furthermore, the following should hold for `int` being any integer value:

```{spec IntSpec.intAddIncreases, int=allIntVals}
int + 1 > int.
self expect: int + 1 toBeKindOf: Integer.
```

And of course, we also expect the following to hold:

```{spec IntSpec.intAddSymmetric, int=allIntVals, arg={allIntVals, allDoubleVals}}
int + arg = (arg + int).
self expect: int + arg toBeKindOf: arg class.
```

##### Subtraction

Subtracting an arbitrary-precision integer from another returns an arbitrary-precision integer.

For example:

```{spec IntSpec.intSubtraction}
 4 - 3 =  1.
-4 - 3 = -7.
```

Subtracting a `Double` from an integer results in a `Double` value.

For example:
```{spec IntSpec.doubleSubtraction}
self expect:  4 - 3.3 toEqual:  0.7 within: 0.00000001.
self expect: -4 - 3.5 toEqual: -7.5 within: 0.00000001.
```

Furthermore, the following should hold for `int` being any integer value:

```{spec IntSpec.intSubDecrease, int=allIntVals}
int - 1 < int.
self expect: int - 1 toBeKindOf: Integer.
```

And of course, we also expect the following to hold:

```{spec IntSpec.intSubAbsSymmetric, int=allIntVals, arg={allIntVals, allDoubleVals}}
(int - arg) abs = (arg - int) abs.
self expect: int - arg toBeKindOf: arg class.
```


[SOM]: http://www.hpi.uni-potsdam.de/hirschfeld/projects/som/
[SOM-st]: https://som-st.github.io
