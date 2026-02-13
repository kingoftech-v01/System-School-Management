"""Demo data generator for library app: Books, BorrowRecords."""

import random
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone

from filieres.models import Filiere
from .models import BookCategory, Publisher, Book, BorrowRecord


BOOKS_DATA = [
    ('Introduction to Algorithms', 'Thomas H. Cormen', '9780262033848'),
    ('Clean Code', 'Robert C. Martin', '9780132350884'),
    ('Design Patterns', 'Erich Gamma', '9780201633610'),
    ('The Art of Computer Programming', 'Donald Knuth', '9780201896831'),
    ('Calculus: Early Transcendentals', 'James Stewart', '9781285741550'),
    ('Linear Algebra Done Right', 'Sheldon Axler', '9783319110790'),
    ('Principles of Economics', 'N. Gregory Mankiw', '9781305585126'),
    ('Organic Chemistry', 'Paula Bruice', '9780134042282'),
    ('Physics for Scientists', 'Raymond Serway', '9781337553278'),
    ('Molecular Biology of the Cell', 'Bruce Alberts', '9780815344322'),
    ('Campbell Biology', 'Lisa Urry', '9780134093413'),
    ('A Brief History of Time', 'Stephen Hawking', '9780553380163'),
    ('The Great Gatsby', 'F. Scott Fitzgerald', '9780743273565'),
    ('To Kill a Mockingbird', 'Harper Lee', '9780061120084'),
    ('1984', 'George Orwell', '9780451524935'),
    ('Operating System Concepts', 'Abraham Silberschatz', '9781119800361'),
    ('Database System Concepts', 'Abraham Silberschatz', '9780078022159'),
    ('Computer Networking', 'James Kurose', '9780133594140'),
    ('Artificial Intelligence', 'Stuart Russell', '9780134610993'),
    ('Data Structures and Algorithms', 'Michael Goodrich', '9781118771334'),
    ('Discrete Mathematics', 'Kenneth Rosen', '9780073383095'),
    ('Probability and Statistics', 'Jay Devore', '9781305251809'),
    ('Engineering Mechanics', 'J.L. Meriam', '9781119390985'),
    ('Thermodynamics', 'Yunus Cengel', '9780073398174'),
    ('Fluid Mechanics', 'Frank White', '9780073398273'),
    ('Principles of Marketing', 'Philip Kotler', '9780134492513'),
    ('Financial Accounting', 'Jerry Weygandt', '9781119594598'),
    ('Management', 'Stephen Robbins', '9780134527604'),
    ('Psychology', 'David Myers', '9781319050627'),
    ('Introduction to Sociology', 'Anthony Giddens', '9780393265163'),
    ('World History', 'William Duiker', '9781337401043'),
    ('Constitutional Law', 'Erwin Chemerinsky', '9781454895749'),
    ('Anatomy and Physiology', 'Elaine Marieb', '9780134156415'),
    ('Fundamentals of Nursing', 'Patricia Potter', '9780323327404'),
    ('Educational Psychology', 'Anita Woolfolk', '9780134774329'),
    ('Research Methods', 'John Creswell', '9781506386768'),
    ('Statistical Methods', 'George Snedecor', '9780813815619'),
    ('Ethics', 'Julia Driver', '9780521544092'),
    ('Philosophy of Science', 'Samir Okasha', '9780198745587'),
    ('Digital Signal Processing', 'John Proakis', '9780133737622'),
    ('Machine Learning', 'Tom Mitchell', '9780070428072'),
    ('Deep Learning', 'Ian Goodfellow', '9780262035613'),
    ('Software Engineering', 'Ian Sommerville', '9780133943030'),
    ('Human Computer Interaction', 'Alan Dix', '9780130461094'),
    ('Embedded Systems', 'James Peckol', '9780471726777'),
    ('Control Systems Engineering', 'Norman Nise', '9781118170519'),
    ('Power Electronics', 'Daniel Hart', '9780073380674'),
    ('Materials Science', 'William Callister', '9781119405498'),
    ('Environmental Science', 'G. Tyler Miller', '9781337569613'),
    ('Biochemistry', 'Jeremy Berg', '9781319114671'),
]


def generate(tenant=None, stdout=None, verbosity=1, context=None, fake=None):
    students = context['accounts']['students']
    total = 0

    categories = list(BookCategory.objects.filter(is_active=True))
    publishers = list(Publisher.objects.all())
    filieres = list(Filiere.objects.all())
    student_users = [s.student for s in students]

    # 1. Books (50)
    books = []
    for i, (title, author, isbn) in enumerate(BOOKS_DATA):
        qty = random.randint(2, 10)
        book = Book.objects.create(
            tenant=tenant,
            title=title,
            author=author,
            isbn=isbn,
            filiere=random.choice(filieres) if filieres else None,
            category=random.choice(categories) if categories else None,
            publisher=random.choice(publishers) if publishers else None,
            publication_year=random.randint(2015, 2025),
            edition=f'{random.randint(1, 8)}th Edition',
            language='English',
            pages=random.randint(200, 1200),
            barcode=f'LIB-{100000 + i}',
            quantity=qty,
            available=random.randint(0, qty),
            shelf_location=f'{chr(65 + (i % 6))}-{random.randint(1, 20):02d}',
            description=fake.paragraph(nb_sentences=2),
        )
        books.append(book)
    total += len(books)

    # 2. Borrow records (80)
    borrows = []
    status_weights = {'borrowed': 0.3, 'returned': 0.5, 'overdue': 0.15, 'lost': 0.05}
    statuses = list(status_weights.keys())
    weights = list(status_weights.values())

    for i in range(80):
        book = random.choice(books)
        student_user = random.choice(student_users)
        status = random.choices(statuses, weights=weights, k=1)[0]
        borrowed_days_ago = random.randint(1, 120)
        due_days = random.randint(14, 30)

        borrow = BorrowRecord.objects.create(
            tenant=tenant,
            book=book,
            student=student_user,
            due_date=(timezone.now() - timedelta(days=borrowed_days_ago - due_days)).date(),
            status=status,
            fine_amount=Decimal(str(round(random.uniform(0, 25), 2))) if status in ('overdue', 'lost') else Decimal('0'),
            notes=fake.sentence() if random.random() < 0.2 else '',
        )
        if status == 'returned':
            borrow.returned_at = timezone.now() - timedelta(days=random.randint(0, borrowed_days_ago))
            borrow.save(update_fields=['returned_at'])
        borrows.append(borrow)
    total += len(borrows)

    if stdout and verbosity >= 1:
        stdout.write(f'  [library] Created {total} records '
                     f'(books: {len(books)}, borrows: {len(borrows)})')

    return {'books': books, '_total': total}
