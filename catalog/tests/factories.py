import factory
from catalog.models import Category, Collection, Media, Product
from factory import Faker
from factory.django import DjangoModelFactory


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    name = Faker("word")
    slug = factory.LazyAttribute(lambda o: o.name.lower().replace(" ", "-"))
    description = Faker("sentence")
    is_active = True
    sort_order = 0


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    title = Faker("sentence", nb_words=3)
    slug = factory.LazyAttribute(lambda o: "-".join(o.title.lower().split()))
    description = Faker("paragraph")
    status = Product.STATUS_PUBLISHED
    default_price = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    currency = Product.CURRENCY_NGN
    seo_title = factory.LazyAttribute(lambda o: o.title)

    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for cat in extracted:
                self.categories.add(cat)


class MediaFactory(DjangoModelFactory):
    class Meta:
        model = Media

    product = factory.SubFactory(ProductFactory)
    url = Faker("image_url")
    alt_text = Faker("sentence")
    is_primary = False
    sort_order = 0


class CollectionFactory(DjangoModelFactory):
    class Meta:
        model = Collection

    name = Faker("word")
    slug = factory.LazyAttribute(lambda o: o.name.lower().replace(" ", "-"))
    description = Faker("sentence")
    is_active = True
    sort_order = 0

    @factory.post_generation
    def products(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for p in extracted:
                self.products.add(p)
