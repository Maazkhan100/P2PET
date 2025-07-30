from typing import List, Dict

# === Offer Object ===
class Offer:
    def __init__(self, user_id: str, role: str, energy: float, price: float):
        self.id = user_id
        self.role = role
        self.energy = energy
        self.price = price

    def __repr__(self):
        return f"Offer({self.id}, {self.role}, {self.energy}kWh @ {self.price})"

# === Greedy Double Auction ===
def greedy_double_auction(offers: List[Offer]) -> List[Dict]:
    # STEP 1: Sort all offers lexicographically by user ID
    offers = sorted(offers, key=lambda x: x.id.lower())  # case-insensitive sorting

    # STEP 2: Sort buyers and sellers by price
    buyers = sorted([o for o in offers if o.role == "buyer"], key=lambda x: -x.price)
    sellers = sorted([o for o in offers if o.role == "seller"], key=lambda x: x.price)

    matches = []
    i, j = 0, 0

    while i < len(buyers) and j < len(sellers):
        buyer = buyers[i]
        seller = sellers[j]

        if buyer.price >= seller.price:
            matched_energy = min(buyer.energy, seller.energy)
            mid_price = round((buyer.price + seller.price) / 2, 2)

            matches.append({
                "buyer_id": buyer.id,
                "seller_id": seller.id,
                "energy_matched": matched_energy,
                "price": mid_price
            })

            # Deduct matched amounts
            buyer.energy -= matched_energy
            seller.energy -= matched_energy

            if buyer.energy == 0:
                i += 1
            if seller.energy == 0:
                j += 1
        else:
            i += 1  # No match, skip to next buyer

    return matches
