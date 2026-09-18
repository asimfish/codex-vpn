#!/usr/bin/env python3
import pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from gateway import serve
serve(str(pathlib.Path(__file__).resolve().parent/'config.json'),('127.0.0.1',47891))
