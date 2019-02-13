from guillotina.component import get_utility
from guillotina.content import create_content_in_container
from guillotina.transactions import managed_transaction
from guillotina.interfaces import IAnnotations
from guillotina.registry import REGISTRY_DATA_KEY
from guillotina_evolution.commands.evolve import EvolveCommand
from guillotina_evolution.utils import register_evolution
from guillotina_evolution.utility import IEvolutionUtility
from guillotina_evolution.utility import GENERATION_KEY
from unittest.mock import Mock


async def test_evolve(loop, environment):
    request, container = environment

    # Create content in the container
    async with managed_transaction(request=request):
        await create_content_in_container(container, "Item", id_="foobar")
        ob = await container.async_get("foobar")
        assert hasattr(ob, "title") is False

    # Register a new evolution
    async def ensure_all_items_have_title(container):
        async for item in container.async_values():
            item.title = ""
            item._p_register()

    utility = get_utility(IEvolutionUtility)

    async with managed_transaction(request=request):
        utility._update_curr_gen(0)

    utility.register(1, ensure_all_items_have_title)

    # Evolve
    async with managed_transaction(request=request):
        await utility.evolve(container)

    # Check objects after evolution
    async with managed_transaction(request=request):
        ob = await container.async_get("foobar")
        assert hasattr(ob, "title") is True
        assert ob.title == ""

    # Assert generation was updated on container registry
    async with managed_transaction(request=request):
        annotations_container = IAnnotations(container)
        registry = await annotations_container.async_get(REGISTRY_DATA_KEY)
        assert registry[GENERATION_KEY] == 1


async def test_evolve_command(environment):
    request, container = environment

    # Create content in the container
    async with managed_transaction(request=request):
        await create_content_in_container(container, "Item", id_="foobar")
        ob = await container.async_get("foobar")
        assert hasattr(ob, "title") is False

    # Register a new evolution
    async def ensure_all_items_have_title(container):
        async for item in container.async_values():
            item.title = ""
            item._p_register()

    utility = get_utility(IEvolutionUtility)

    async with managed_transaction(request=request):
        utility._update_curr_gen(0)

    utility.register(1, ensure_all_items_have_title)

    command = EvolveCommand()
    command.request = request
    await command.run(Mock, Mock, Mock)

    # Check objects after evolution
    async with managed_transaction(request=request):
        ob = await container.async_get("foobar")
        assert hasattr(ob, "title") is True
        assert ob.title == ""


async def test_registry(environment):
    request, _ = environment
    utility = get_utility(IEvolutionUtility)

    async with managed_transaction(request=request):
        assert utility._get_curr_gen() == 0

    async with managed_transaction(request=request):
        utility._update_curr_gen(5)

    registry = request.container_settings
    registry[GENERATION_KEY] == 5


def test_register_decorator():
    @register_evolution(1)
    async def migration_step(container):
        pass

    utility = get_utility(IEvolutionUtility)
    assert utility._evolvers == {1: migration_step}
