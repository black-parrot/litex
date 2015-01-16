import time
import argparse
from config import *

logical_sector_size = 512

class SATABISTDriver:
	def __init__(self, regs, name):
		self.regs = regs
		self.name = name
		self.frequency = regs.identifier_frequency.read()
		self.time = 0
		for s in ["start", "sector", "count", "random", "done", "errors", "cycles"]:
			setattr(self, s, getattr(regs, name + "_"+ s))

	def run(self, sector, count, random):
		self.sector.write(sector)
		self.count.write(count)
		self.random.write(random)
		self.start.write(1)
		while (self.done.read() == 0):
			pass
		self.time = self.cycles.read()/self.frequency
		speed = (count*logical_sector_size)/self.time
		errors = self.errors.read()
		return (speed, errors)

class SATABISTGeneratorDriver(SATABISTDriver):
	def __init__(self, regs, name):
		SATABISTDriver.__init__(self, regs, name + "_generator")

class SATABISTCheckerDriver(SATABISTDriver):
	def __init__(self, regs, name):
		SATABISTDriver.__init__(self, regs, name + "_checker")

KB = 1024
MB = 1024*KB
GB = 1024*MB

# Note: use IDENTIFY command to find numbers of sectors
hdd_max_sector = (32*MB)/logical_sector_size

def _get_args():
	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
		description="""\
SATA BIST utility.
""")
	parser.add_argument("-s", "--transfer_size", default=4, help="transfer sizes (in MB, up to 16MB)")
	parser.add_argument("-l", "--total_length", default=256, help="total transfer length (in MB, up to HDD capacity)")
	parser.add_argument("-r", "--random", action="store_true", help="use random data")
	parser.add_argument("-c", "--continuous", action="store_true", help="continuous mode (Escape to exit)")
	return parser.parse_args()

if __name__ == "__main__":
	args = _get_args()
	wb.open()
	###
	generator = SATABISTGeneratorDriver(wb.regs, "sata_bist")
	checker = SATABISTCheckerDriver(wb.regs, "sata_bist")

	sector = 0
	count = int(args.transfer_size)*MB//logical_sector_size
	length = int(args.total_length)*MB
	random = int(args.random)
	continuous = int(args.continuous)
	try:
		while (sector*logical_sector_size < length) or continuous:
			# generator (write data to HDD)
			write_speed, write_errors = generator.run(sector, count, random)

			# checker (read and check data from HDD)
			read_speed, read_errors = checker.run(sector, count, random)

			print("sector=%d write_speed=%4.2fMB/sec read_speed=%4.2fMB/sec errors=%d" %(sector, write_speed/MB, read_speed/MB, write_errors + read_errors))
			sector += count

	except KeyboardInterrupt:
		pass
	###
	wb.close()
