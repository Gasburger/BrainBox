function result = process_data(data_in)

data = uint8(data_in);

if (length(findstr(data,'StartUp!')) == 1)
    % Eliminate 'StartUp!' string with new line characters (8+2)
    data = data(findstr(data,'StartUp!')+10:end);
end

% Unpacking data from frames:
result = [];
i = 1;
while i < length(data)-1
    if uint8(data(i)) > 127
        % Found beginning of frame
        % Extract one sample from 2 bytes
        intout = uint16(uint16(bitand(uint8(data(i)),127)).*128);
        i = i + 1;
        intout = intout + uint16(uint8(data(i)));
        result = [result, intout];
    end
    i = i + 1;
end

end