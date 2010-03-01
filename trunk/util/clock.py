# Funciones comunes de manejo de tiempo
# -*- coding: utf-8 -*-

from time import time, gmtime, strftime

def min_format(seconds = None):
    """@brief Devuelve una cadena formateada con los míninimos elementos del
    tiempo dado en segundos. Por ejemplo: 
        min_format(65) == '1 m 5s'
    Si el tiempo en segundos es superior a un año, se considera un timestamp y
    se devuelve la fecha en este formato:
        min_format(1267477038.928261) == '1-3-2010 20:58:22'

    Si no se especifica el argumento seconds, se usa el valor devuelto por
    time.time()
    @param seconds (Optional)Number of seconds.
    @retval A string with the date if seconds > year, minimal timecount
    otherwhise
    """

    if seconds is None :
        seconds = time()

    # time.struct_time(tm_year2010, tm_mon=3, tm_mday=1, tm_hour=20, tm_min=57,
    # tm_sec=30, tm_wday=0, tm_yday=60, tm_isdst=0) ( 1-3-2010 at 20:57:30 ) 
    # 0. year 1. month 2. day of month 3. hours 4. minutes 5. seconds
    ldate = gmtime(seconds)
    strfmt = "%d-%m-%Y %H:%M:%S"

    if seconds <  31536000 :  # Less than a year
        strfmt = ""

        # More than a day
        if seconds > 86400 :
            # -1 day to compensate that starts at 1
            strfmt += "%i d " % (ldate[2] - 1)

        # More than an hour
        if seconds > 3600 :
            strfmt += "%i h " % ldate[3]

        # More than a minute
        if seconds > 60 : 
           strfmt += "%i m " % ldate[4]

        # Seconds always are in the timecount
        strfmt += "%i s" % ldate[5]

    return strftime(strfmt, ldate)

# Tests
if __name__ == "__main__" :

    # Actual time
    print "Actual time"
    print min_format(time())
    # 1267478253.700711  --> '01-03-2010 21:17:33'
    print "First of march of 2010 at 21:17:33 '01-03-2010 21:17:33'"
    print min_format(1267478253.700711)

    # twenty seconds
    print "twenty seconds"
    print min_format(20)

    # twenty minutes and twenty seconds
    print "twenty minutes and twenty seconds"
    print min_format(60 * 20 + 20)

    # twenty hours, twenty minutes and twenty seconds
    print "twenty hours, twenty minutes and twenty seconds"
    print min_format(3600 * 20 + 60 * 20 + 20)

    # twenty days twenty hours, twenty minutes and twenty seconds
    print "twenty days, twenty hours, twenty minutes and twenty seconds"
    print min_format(86400 * 20 + 3600 * 20 + 60 * 20 + 20)
