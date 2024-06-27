import django_rq
import os

# if __name__ == '__main__':
#     os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'review_algorithm.settings')
#     django_rq.worker.run_worker('default')
import django_rq

queue = 'default'
django_rq.workers.run_worker(queue)