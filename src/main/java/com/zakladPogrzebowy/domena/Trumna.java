package com.zakladPogrzebowy.domena;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import javax.persistence.CascadeType;
import javax.persistence.Entity;
import javax.persistence.FetchType;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.NamedQueries;
import javax.persistence.NamedQuery;
import javax.persistence.OneToMany;
import javax.validation.constraints.Min;
import javax.validation.constraints.Size;


@Entity
@NamedQueries({ 
	@NamedQuery(name = "trumna.wszystkie", query = "Select t from Trumna t"),
	@NamedQuery(name = "trumna.dostepne", query = "Select t from Trumna t where t.ilosc <> 0")
})
public class Trumna {
	
	private Long id;
	private String rodzaj = "";
	private Double cena = 0.0;
	private Integer ilosc = 0;

	private List<Pogrzeb> pogrzeby = new ArrayList<Pogrzeb>();


	public Trumna() {
	}

	public Trumna(String rodzaj, Double cena, Integer ilosc) {
	this.rodzaj = rodzaj;
	this.cena = cena;
	this.ilosc = ilosc;
	}
	
	@Id
	@GeneratedValue(strategy = GenerationType.AUTO)
	public Long getId() {
		return id;
	}
	public void setId(Long id) {
		this.id = id;
	}


	@OneToMany(mappedBy = "pogrzeb", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
	public List<Pogrzeb> getPogrzeby() {
	return pogrzeby;
	}
	public void setPogrzeby(List<Pogrzeb> pogrzeby) {
	this.pogrzeby = pogrzeby;
	}


	@Size(min = 2)
	public String getRodzaj() {
		return rodzaj;
	}
	public void setRodzaj(String rodzaj) {
		this.rodzaj = rodzaj;
	}

	@Min(0)
	public Double getCena() {
		return cena;
	}
	public void setCena(Double cena) {
		this.cena = cena;
	}

	@Min(0)
	public Integer getIlosc() {
		return ilosc;
	}
	public void setIlosc(Integer ilosc) {
		this.ilosc = ilosc;
	}
}
