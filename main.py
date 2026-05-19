from extractor import run_extraction

if __name__ == "__main__":
    data = run_extraction()
    print(f"\nDonnees pretes :")
    print(f"  - {len(data['tracks'])} tracks brutes")
    print(f"  - {len(data['tracks_detail'])} tracks détaillées")
    print(f"  - {len(data['artists'])} artistes bruts")
    print(f"  - {len(data['artists_detail'])} artistes détaillés")
    print(f"\nFichiers JSON sauvegardes dans : data/raw/")