import numpy as np
import math

def implied_probability(odds: int):
   if(odds < 0):
      return 1 / (1 - 100 / odds)
   else:
      return 1 / (1 + odds / 100)
   
def expected_value(odds: int, probability: float):
   if odds < 0:
      frac = -100 / odds
   else:
      frac = odds / 100
   print('here')
   print(frac)
   print(probability)
   print(frac * probability)
   ev = (frac * probability) - (1 - probability)
   return ev