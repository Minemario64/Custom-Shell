# Spec for Conditionals and Loops in csh 2.0

## IF Statement

Syntax:
```
if <condition>:
    <command(s)>
end
```

Examples:
```
if [ ${USER} = "root" ]:
    echo "Running As Root"
end
```
```
if <path -f ${1}>:
    cat ${1}
end
```

### If Chain

Syntax:
```
if <condition>:
    <command(s)>
elif <condition>:
    <command(s)>
else:
    <command(s)>
end
```

Examples:
```
if <path -f ${1}>:
    cat ${1}
elif <path -d ${1}>:
    ls ${1}
else:
    echo "Path '${1}' doesn't exist"
end
```
```
if ( ${1} > 10 ):
    echo "Greater Than 10"
else:
    echo "Less Than or equal to 10"
end
```

## FOR Loops

Syntax:
```
for <var-name> in <list> <if custom sep instead of '|', 'sep <sep-string>'>:
    <command(s)>
end
```

Examples:
```
for arg in ${*} sep " ":
    mcd ${arg}
    git init
    cd -
end
```
```
for path in ${PATH}:
    ls -a ${path}
end
```

## While Loops

Syntax:
```
while <condition>:
    <command(s)>
end
```

Examples:
```
var counter=5
while ( ${counter} > 0):
    echo ${counter}
    var counter=((${counter} - 1))
end
```
```
while [ true ]:
    input input "Enter Command (q to quit):"
    if [ ${input} = "q" ]:
        break
    end
    echo ${input}
end
```