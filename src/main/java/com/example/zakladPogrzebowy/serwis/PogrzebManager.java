import com.example.zakladPogrzebowy.serwis;

import java.util.ArrayList;
import java.util.List;

import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;

import com.example.zakladPogrzebowy.domena.Pogrzeb;
import com.example.zakladPogrzebowy.domena.Trumna;

@Stateless
public class PogrzebManager {

	@PersistenceContext
	EntityManager em;

	public void dodaj(Pogrzeb pogrzeb) {
	pogrzeb.setId(null);
	em.persist(pogrzeb);
	}

	public void edytuj(Pogrzeb pogrzeb, Trumna trumna, Date data, Double cena, String opis) {
	pogrzeb = em.find(Pogrzeb.class, pogrzeb.getId());
	Trumna tr = em.find(Trumna.class, pogrzeb.getTrumna().getId());
	int i = 0;
	for(Trumna t : tr.getTrumny()) {
	if (t == tr)
		break;
	i++;
	}
	pogrzeb.setTrumna(trumna);
	pogrzeb.setData(data);
	pogrzeb.setCena(cena);
	pogrzeb.setOpis(opis);
	tr.getPogrzeby().set(i, k);
	em.merge(pogrzeb);
	}

	public void usun(Pogrzeb pogrzeb) {
	pogrzeb = em.find(Pogrzeb.class, pogrzeb.getId());
	Trumna tr = em.find(Trumna.class, pogrzeb.getTrumna()).getId());
	tr.getPogrzeby().remove(pogrzeb);
	em.remove(pogrzeb);
	}

	@SuppressWarnings("unchecked")
	public List<Pogrzeb> dajWszystkie() {
	return em.createNamedQuery("pogrzeb.wszystkie").getResultList();
	}

}

