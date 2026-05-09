import AnomalySection from "@/components/AnomalySection";
import BookingTable from "@/components/BookingTable";
import DuplicateSection from "@/components/DuplicateSection";
import ManualSection from "@/components/ManualSection";

export default function Home() {
  return (
    <main className="container">
      <header className="page-header">
        <h1>Booking Insights</h1>
        <p>Journal entry review workspace for accounting postings.</p>
      </header>

      <section>
        <h2>Entries</h2>
        <BookingTable />
      </section>

      <section>
        <h2>Anomalies</h2>
        <AnomalySection />
      </section>

      <section>
        <h2>Possible Duplicates</h2>
        <DuplicateSection />
      </section>

      <section>
        <h2>Booking Manual</h2>
        <ManualSection />
      </section>
    </main>
  );
}
