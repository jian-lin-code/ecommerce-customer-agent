import importlib
import inspect
import pkgutil
from task.action.runner import ActionRunner
from task.action.registry import ActionRegistry
from task.action.base import Action
from task.action.builtin.action_listen import ActionListen
from task.action.builtin.action_response import ActionResponse


def register_builtin_actions(action_runner: ActionRunner):
    """
    注册内置的action：手动 register
    :param action_runner:
    :return:
    """
    action_listen = ActionListen()
    action_response = ActionResponse()
    action_runner.registry.register(action_listen)
    action_runner.registry.register(action_response)


def register_custom_actions(action_runner: ActionRunner):
    """
    扫描指定包，完成 Action子类的自动注册
    :param action_runner:
    :return:
    """

    package = importlib.import_module("task.action.custom")

    for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__, prefix=f"{package.__name__}."):

        # 只处理模块文件，不处理子包
        if is_pkg:
            continue
        module = importlib.import_module(module_name)
        for _, clz in inspect.getmembers(module, inspect.isclass):

            # 只要 Action 的子类，排除基类本身
            if not issubclass(clz, Action) or clz is Action:
                continue

            # 只注册"在这个模块里定义的"类，排除 import 进来的
            # 如 LookUpOrderStatusAction 被 lookup_logistics.py import 时不重复注册
            if clz.__module__ != module.__name__:
                continue
            action_runner.registry.register(clz())

def build_action_runner() -> ActionRunner:
    action_runner = ActionRunner(ActionRegistry())
    register_builtin_actions(action_runner)
    register_custom_actions(action_runner)
    return action_runner

if __name__ == '__main__':

     build_action_runner()