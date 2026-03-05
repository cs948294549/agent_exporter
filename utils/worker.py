from concurrent.futures.thread import ThreadPoolExecutor
import functools

def execAllFunctions(tasks, max_workers=8):
    result = {}
    def cb(future, name):
        stdout = future.result()
        result[name] = stdout

    with ThreadPoolExecutor(max_workers=max_workers) as p:
        # 提交任务
        for task in tasks:
            future = p.submit(task["func"], *task["args"], **task["kwargs"])
            future.add_done_callback(functools.partial(cb, name=task["name"]))
    return result


if __name__ == "__main__":
    pass