String data ;
int relay = 7;
void setup()
{
  pinMode(relay, OUTPUT);
  digitalWrite(relay, LOW);
  Serial.begin(9600);
}
void loop()
{
  if (Serial.available() > 0)
  {
    data = Serial.readStringUntil('\n');
    if (data == "on")
    {
      digitalWrite(relay, HIGH);
    }
    if (data == "off")
    {
      digitalWrite(relay, LOW);
    }
  }
}
