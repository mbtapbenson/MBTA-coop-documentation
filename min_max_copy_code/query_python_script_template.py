import sys
import ducktape

if not sys.argv[1]:
    raise ValueError('Please provide a date string as argument')

date = sys.argv[1]

# Use the same setname as the shell script
dlpath = '/home/rubix/Desktop/Project-Ducttape/data/setname/' + date + '/'

display, browser = ducktape.chrome_initialize(dlpath)
ducktape.fmis_login(browser)
ducktape.fmis_get_direct_query(browser, 'QUERY_NAME')
ducktape.wait_for_file(dlpath)
ducktape.chrome_close(display, browser)