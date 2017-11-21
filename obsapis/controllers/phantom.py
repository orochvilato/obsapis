from selenium import webdriver
import signal
import time
#driver.service.process.send_signal(signal.SIGTERM) # kill the specific phantomjs child proc
#~driver.quit()                                      # quit the node proc
class phantomjs:
    def __init__(self,nb=1):
        self.nbproc = nb
        self.processes = []
        self.ready = [True]*nb
        for i in range(nb):
            p = "Test" # self.spawn()
            self.processes.append(p)
            pass
    def spawn(self):
        return webdriver.PhantomJS()

    def _schedule(foo):
        def magic( self,*args,**kwargs ) :
            print "start magic"
            print self.ready
            i = 0
            while not self.ready[i]:
                for i in range(self.nbproc):
                    if self.ready[i]:
                        break

                if self.ready[i]:
                    break
                time.sleep(0.2)
                i = 0

            self.ready[i] = False
            try:
                result = foo( self,self.processes[i],*args,**kwargs )
            except:
                pass
            self.ready[i] = True

            print "end magic"
        return magic

    @_schedule
    def test(self,proc,*args,**kwargs):
        print proc
        time.sleep(10)
        return "toto"

p = phantomjs()
print p.test('1','2',t=6)
print p.test('1','2',t=6)
