from guillotina.component import get_utility
from guillotina.content import create_content_in_container
from guillotina.transactions import managed_transaction
from guillotina.interfaces import IAnnotations
from guillotina.registry import REGISTRY_DATA_KEY
from guillotina_evolution.utility import IEvolutionUtility
from guillotina_evolution.utility import GENERATION_KEY


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
    utility.register(1, ensure_all_items_have_title)

    # Evolve
    async with managed_transaction(request=request):
        await utility.evolve(container)

    # Check objects after evolution
    async with managed_transaction(request=request):
        ob = await container.async_get("foobar")
        assert hasattr(ob, "title") is True
        assert ob.title == ""

    async with managed_transaction(request=request):
        annotations_container = IAnnotations(container)
        registry = await annotations_container.async_get(REGISTRY_DATA_KEY)
        assert registry[GENERATION_KEY] == 1
