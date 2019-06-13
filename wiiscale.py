#!/usr/bin/env python3

import cwiid
import pygame
from pygame.locals import *
import threading
import datetime

def weight( reading, cal_arr ):
  if reading < cal_arr[0]: return 0
  if reading < cal_arr[1]:
    return float(reading - cal_arr[0]) / float(cal_arr[1]-cal_arr[0]) * 17.0
  return float(reading - cal_arr[1]) / float(cal_arr[2]-cal_arr[1]) * 17.0 + 17.0

def get_avg_mass():
  if len(mass_readings) == 0: return 0
  avg_mass = 0
  for v in mass_readings: avg_mass += v
  avg_mass /= len(mass_readings)
  d_avg_mass = avg_mass - offset_mass
  if d_avg_mass < 0: d_avg_mass = 0
  return d_avg_mass


offset_y = 0
def pygame_writeline( status_str ):
  global offset_y
  text = font.render( status_str, 1, (255,255,255) )
  textpos = text.get_rect()
  textpos.top = offset_y
  offset_y += textpos.height
  screen.blit(text,textpos)

class FindWiimote(threading.Thread):
  attempt_count = 0
  wiimote = None
  named_calibration = {}

  def run(self):
    FindWiimote.wiimote = None
    try:
      print("looking for wiimote")
      FindWiimote.wiimote = cwiid.Wiimote()
      print("wiimote found")
      FindWiimote.wiimote.rpt_mode = cwiid.RPT_BALANCE | cwiid.RPT_BTN
      FindWiimote.wiimote.led = cwiid.LED1_ON
      balance_calibration = FindWiimote.wiimote.get_balance_cal()
      FindWiimote.named_calibration = { 'right_top': balance_calibration[0], 'right_bottom': balance_calibration[1], 'left_top': balance_calibration[2], 'left_bottom': balance_calibration[3] }
    except RuntimeError as e:
      print("Unable to find wiimote")
      FindWiimote.wiimote = None
    FindWiimote.attempt_count += 1

pygame.init()
pygame.display.set_caption("wiiscale 2 - Adrian Cheater")
screen = pygame.display.set_mode( (640, 480), 0 ) 

font = pygame.font.Font(None,36)

findThread = None
exit = False
mass_readings = []
avg_mass = 0
offset_mass = 0
while not exit:
  for evt in pygame.event.get():
    if evt.type == QUIT: exit = True
    if evt.type == KEYDOWN:
      if evt.key == K_z:
        offset_mass = 0
        for v in mass_readings:
          if v > offset_mass: offset_mass = v
      if evt.key == K_w:
        with open("records.csv", "a") as f:
          f.write( "%s, %0.2f\n" % (datetime.datetime.utcnow(),get_avg_mass()) ) 

  screen.fill((0,0,0))
  offset_y = 0
  if FindWiimote.wiimote:
    pygame_writeline( "Balance Board Status:")
    try:
      if FindWiimote.wiimote.state['buttons'] & cwiid.BTN_A: exit = True
    except KeyError:
      pass
    try:
      pygame_writeline("battery: %0.0f%%" % ( FindWiimote.wiimote.state['battery'] * 100.0 / cwiid.BATTERY_MAX ))
    except KeyError:
      pygame_writeline("battery: unknown")
    try:
      total_mass = 0
      for key,value in FindWiimote.wiimote.state['balance'].items():
        total_mass += weight(value,FindWiimote.named_calibration[key])
        pygame_writeline( "%s %s (%s) %s" % (key,value,FindWiimote.named_calibration[key],weight(value,FindWiimote.named_calibration[key]) ) )
      total_mass
      d_mass = total_mass - offset_mass
      if d_mass < 0: d_mass = 0
       
      if len(mass_readings) == 0 or total_mass != mass_readings[-1]: mass_readings.append( total_mass )
      while len(mass_readings) > 100: mass_readings.pop(0)

      pygame_writeline( "offset mass: %0.1f kg" % offset_mass )
      pygame_writeline( "mass: %0.1f kg %0.2f lbs" % (d_mass,d_mass*2.20462) )
      d_avg_mass = get_avg_mass()
      pygame_writeline( "avg mass: %0.1f kg %0.2f lbs" % (d_avg_mass,d_avg_mass*2.20462) )
    except KeyError:
      pygame_writeline( "balance: unknown" )
  else:
    pygame_writeline("Looking for wiimote... attempt %i" % FindWiimote.attempt_count)
    if not findThread:
      findThread = FindWiimote()
      print("starting search thread")
      findThread.start()
    elif not findThread.isAlive():
      print("Killing finished thread")
      findThread = None
      print("Wiimote status %s" % FindWiimote.wiimote)

  pygame.display.flip()


print("shutting down")
pygame.quit()
#if wiimote:
#  wiimote.disable( cwiid.FLAG_MESG_IFC )
#  wiimote.mesg_callback = None
#  wiimote = None
