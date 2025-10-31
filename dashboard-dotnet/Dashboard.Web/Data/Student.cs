// Data/Student.cs
namespace Dashboard.Web.Data
{
    public class Student
    {
        public int Id { get; set; }
        public string Name { get; set; } = string.Empty;
        public string StudentNumber { get; set; } = string.Empty;

        // Bir öğrencinin birden fazla olayı olabilir
        public ICollection<EventLog> EventLogs { get; set; } = new List<EventLog>();
    }
}