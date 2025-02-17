import React, { useState } from 'react';
import '../styles/calculator.css';

// Define types for clarity
type Operation = '+' | '-' | '*' | '/' | null;

const Calculator: React.FC = () => {
  const [display, setDisplay] = useState<string>('0');
  const [currentOperation, setCurrentOperation] = useState<Operation>(null);
  const [previousValue, setPreviousValue] = useState<number | null>(null);

  const handleNumberClick = (number: string) => {
    // If display is '0' or we're starting a new calculation, replace the display
    setDisplay(prev => prev === '0' ? number : prev + number);
  };

  const handleOperationClick = (operation: Operation) => {
    // Store the current value and operation
    setPreviousValue(parseFloat(display));
    setCurrentOperation(operation);
    setDisplay('0');
  };

  const handleEqualClick = () => {
    if (currentOperation && previousValue !== null) {
      let result: number;
      switch (currentOperation) {
        case '+':
          result = previousValue + parseFloat(display);
          break;
        case '-':
          result = previousValue - parseFloat(display);
          break;
        case '*':
          result = previousValue * parseFloat(display);
          break;
        case '/':
          result = previousValue / parseFloat(display);
          break;
        default:
          return;
      }
      setDisplay(result.toString());
      setCurrentOperation(null);
      setPreviousValue(null);
    }
  };

  const handleClearClick = () => {
    setDisplay('0');
    setCurrentOperation(null);
    setPreviousValue(null);
  };

  return (
    <div className="calculator">
      <div className="display">{display}</div>
      <div className="buttons">
        {['7', '8', '9', '/', '4', '5', '6', '*', '1', '2', '3', '-', '0', '.', '=', '+'].map((btn, index) => (
          <button key={index} onClick={() => {
            if (btn === '=') handleEqualClick();
            else if (btn === '+' || btn === '-' || btn === '*' || btn === '/') handleOperationClick(btn as Operation);
            else handleNumberClick(btn);
          }}>{btn}</button>
        ))}
        <button onClick={handleClearClick}>C</button>
      </div>
    </div>
  );
};

export default Calculator;