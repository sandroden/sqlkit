"""Regressione: discard di una riga nuova su collection del leader invalidata.

Bug osservato in pysia: creando una riga dettaglio (o2m) nuova e vuota e
cambiando selezione, ``record_save(discard_unchanged=True)`` faceva
``session.expunge(obj)`` + ``self.records.remove(obj)``.  Se un save
precedente aveva gia' fatto ``session.expire`` del leader, la collection a cui
``self.records`` puntava era invalidata: la ``.remove()`` faceva scattare il
backref di SQLAlchemy -> ``KeyError`` sul nome della relazione + SAWarning
"This collection has been invalidated".

Questi test riproducono la meccanica di sessione senza GTK e verificano il
comportamento della strategia di rimozione adottata in
``table._discard_new_from_records``: lavorare sulla collection *viva* del
leader anziche' sul riferimento stale.
"""
import warnings
from decimal import Decimal

import pytest
from sqlalchemy import Column, ForeignKey, Integer, Numeric, String, create_engine
from sqlalchemy.orm import Session, declarative_base, relationship

Base = declarative_base()


class Giorno(Base):
    __tablename__ = "sk_disc_giorno"
    id = Column(Integer, primary_key=True)


class Real(Base):
    __tablename__ = "sk_disc_real"
    id = Column(Integer, primary_key=True)
    qta = Column(Numeric(8, 2), nullable=False)
    descr = Column(String(200))
    giorno_id = Column(Integer, ForeignKey("sk_disc_giorno.id"))
    giorno = relationship("Giorno", backref="ore")


@pytest.fixture
def seeded():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = Session(engine)
    g = Giorno(id=1)
    session.add(g)
    session.add(Real(id=1, qta=Decimal("2"), descr="prima", giorno=g))
    session.commit()
    yield session, g
    session.close()
    engine.dispose()


def _make_new_row(session, g):
    """Nuova riga vuota (qta non compilata) in session.new, come da UI."""
    r_new = Real(id=2, giorno=g)
    session.add(r_new)
    assert r_new in session.new
    return r_new


def test_stale_records_remove_reproduces_keyerror(seeded):
    """Documenta il bug: .remove() sul riferimento stale -> KeyError('ore')."""
    session, g = seeded
    records = g.ore  # cio' che sqlkit tiene come self.records
    r_new = _make_new_row(session, g)

    session.expire(g)  # come record_save:918 dopo un save riuscito
    session.expunge(r_new)  # come record_save:877

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with pytest.raises(KeyError):
            records.remove(r_new)  # come record_save:878 (vecchio comportamento)


def test_live_collection_remove_is_clean(seeded):
    """Il fix: rifetchare la collection viva dal leader non solleva nulla."""
    session, g = seeded
    _stale = g.ore
    r_new = _make_new_row(session, g)

    session.expire(g)
    session.expunge(r_new)

    # replica _discard_new_from_records: getattr rilazy-loada e ripopola __dict__
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # nessun SAWarning atteso
        coll = getattr(g, "ore", None)
        assert coll is not None
        if r_new in coll:
            coll.remove(r_new)

    # r_new gia' expunged: non deve piu' comparire; resta solo la riga salvata
    assert [r.id for r in g.ore] == [1]
