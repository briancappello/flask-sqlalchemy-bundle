** ideally everything should be lazy-mapped by default **
    > HOWEVER, events do not seem to work with lazy-mapping. so need to figure
    that out

##### * improve the lazy relationships shit for advanced model structures
    > build up a directed graph using networkx, figure out which models to
      register that way

## MetaOptions should be instantiated once in model_meta_options and imported into model_meta_factory, instead of creating a new one for each and every new Model

* better docs for individual meta options (docstrings would be a good start)

* investigate if it's possible to improve the slugify/events experience by using meta options

* improve reversible op migrations (only used by materialized views at the moment)
  - pretty sure it needs some kind of way to lookup which revision contains the
    prior reversible op declaration for the table that's being migrated

* improve docs for performing data migrations, dealing with nullable -> not null, etc

* document lazy_mapped, bundle inheritance and overriding behavior
    > esp quirks regarding relationships and backref

* investigate validation
  > moonshot goal is something that works below both Flask-WTF and Marshmallow,
    allowing for DRY validation whether using forms or an API
