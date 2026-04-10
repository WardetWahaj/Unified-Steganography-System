"""
RQ Worker for Steganography Tasks
===================================
Picks up jobs from the 'steganography' Redis queue and processes them.

Usage:
  rq worker steganography --url redis://localhost:6379/0
  OR
  python worker.py
"""
import os
import sys

if __name__ == '__main__':
    from redis import Redis
    from rq import Worker, Queue

    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    conn = Redis.from_url(redis_url)

    print("[*] Starting Steganography Worker...")
    from api.app import stego  # Pre-import

    queues = [Queue('steganography', connection=conn)]
    worker = Worker(queues, connection=conn)
    print("[+] Steganography Worker ready and listening...")
    worker.work()
